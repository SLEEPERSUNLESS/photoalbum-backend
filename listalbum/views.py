from django.shortcuts import render, get_object_or_404
from django.db import models
from django.utils.text import slugify
from rest_framework.response import Response
from .models import Photo, Album, AlbumAccess, Order
from .serializers import PhotosSerializer, AlbumSerializer, OrderSerializer
from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .pagination import AlbumPagination
from user_app.models import AllowedEmail
import requests
from django.conf import settings
import uuid


class PhotoAlbumAV(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlbumSerializer
    pagination_class = AlbumPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        # staff users can see everything; regular users see only their albums
        # or albums where their email has been granted explicit access
        user = self.request.user
        qs = Album.objects.all().order_by("-created_at")
        if user.is_staff:
            return qs
        email = getattr(user, 'email', None)
        if not email:
            return qs.none()
        return qs.filter(models.Q(owner=user) | models.Q(accesses__email__iexact=email)).distinct()

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_staff:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        title = (request.data.get("title") or "").strip()
        description = (request.data.get("description") or "").strip()
        thumbnail = request.FILES.get("thumbnail")

        if not title:
            return Response({"detail": "title is required"}, status=status.HTTP_400_BAD_REQUEST)

        owner = user

        base = slugify(title) or "album"
        slug = base
        i = 2
        while Album.objects.filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1

        album = Album(title=title, description=description, owner=owner, slug=slug)
        album.save()
        if thumbnail:
            album.thumbnail = thumbnail
            album.save(update_fields=["thumbnail"])

        files = request.FILES.getlist('photos') or []
        single = request.FILES.get('photo')
        if single:
            files.append(single)
        for f in files:
            fname = (getattr(f, 'name', '') or '').rsplit('.', 1)[0] or 'photo'
            Photo.objects.create(album=album, url=f, title=fname)

        serializer = self.serializer_class(album)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    

class AlbumPhotoListView(generics.ListAPIView): # allow post here later
    permission_classes = [IsAuthenticated]
    serializer_class = PhotosSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        slug = self.kwargs['slug']
        user = self.request.user
        qs = Photo.objects.filter(album__slug=slug)
        # if user is staff they can see photos in any album; otherwise ensure
        # the album belongs to them or access granted for their email
        if user.is_staff:
            return qs
        email = getattr(user, 'email', None)
        if not email:
            return qs.none()
        return qs.filter(models.Q(album__owner=user) | models.Q(album__accesses__email__iexact=email)).distinct()

    def list(self, request, *args, **kwargs):
        slug = self.kwargs['slug']
        album = get_object_or_404(Album, slug=slug)
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'title': album.title,
            'photos': serializer.data
        })

    def post(self, request, *args, **kwargs):
        # Admin-only: bulk add photos to album
        user = request.user
        if not user.is_staff:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        slug = self.kwargs['slug']
        album = get_object_or_404(Album, slug=slug)

        files = request.FILES.getlist('photos') or []
        # also accept single file under 'photo'
        single = request.FILES.get('photo')
        if single:
            files.append(single)
        if not files:
            return Response({"detail": "No photos provided"}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        for f in files:
            title = (getattr(f, 'name', '') or '').rsplit('.', 1)[0] or 'photo'
            p = Photo.objects.create(album=album, url=f, title=title)
            created.append(p)
        data = PhotosSerializer(created, many=True).data
        return Response(data, status=status.HTTP_201_CREATED)


from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response


@api_view(["GET", "POST"])  
@permission_classes([IsAuthenticated, IsAdminUser])
def album_access_view(request, slug):
    album = get_object_or_404(Album, slug=slug)
    if request.method == "GET":
        items = album.accesses.all().order_by('email')
        return Response([
            {"id": it.id, "email": it.email, "created_at": it.created_at}
            for it in items
        ])
    # POST
    email = (request.data.get("email") or "").strip().lower()
    if not email:
        return Response({"detail": "email required"}, status=status.HTTP_400_BAD_REQUEST)
    obj, created = AlbumAccess.objects.get_or_create(album=album, email=email)
    return Response({"id": obj.id, "email": obj.email}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(["DELETE"])  
@permission_classes([IsAuthenticated, IsAdminUser])
def album_access_delete(request, slug, pk: int):
    album = get_object_or_404(Album, slug=slug)
    try:
        item = AlbumAccess.objects.get(pk=pk, album=album)
    except AlbumAccess.DoesNotExist:
        return Response(status=status.HTTP_204_NO_CONTENT)
    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["DELETE"])  
@permission_classes([IsAuthenticated, IsAdminUser])
def album_photo_delete(request, slug, pk: int):
    album = get_object_or_404(Album, slug=slug)
    try:
        photo = Photo.objects.get(pk=pk, album=album)
    except Photo.DoesNotExist:
        return Response(status=status.HTTP_204_NO_CONTENT)
    photo.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def email_suggestions(request):
    q = request.GET.get('q', '').strip().lower()
    if not q:
        return Response([])
    
    from django.contrib.auth import get_user_model
    from django.db.models import Q
    User = get_user_model()
    
    allowed = AllowedEmail.objects.filter(
        email__icontains=q, is_active=True
    ).values_list('email', flat=True)[:10]
    
    admins = User.objects.filter(
        Q(is_staff=True) | Q(is_superuser=True),
        email__icontains=q
    ).values_list('email', flat=True)[:10]
    
    suggestions = list(set(allowed) | set(admins))
    suggestions.sort()
    
    return Response(suggestions[:10])


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def album_meta_view(request, slug):
    album = get_object_or_404(Album, slug=slug)

    if request.method == "GET":
        serializer = AlbumSerializer(album)
        return Response(serializer.data)

    if request.method == "DELETE":
        album.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    title = request.data.get("title")
    description = request.data.get("description")
    thumbnail = request.FILES.get("thumbnail")

    changed = False
    update_fields = []
    if title is not None:
        album.title = title
        update_fields.append("title")
        changed = True
    if description is not None:
        album.description = description
        update_fields.append("description")
        changed = True
    if changed:
        album.save(update_fields=update_fields)
    if thumbnail is not None:
        album.thumbnail = thumbnail
        album.save(update_fields=["thumbnail"]) 

    serializer = AlbumSerializer(album)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment(request):
    serializer = OrderSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    order = serializer.save()
    
    payu_order_id = str(uuid.uuid4())
    order.payu_order_id = payu_order_id
    order.save()
    
    order_data = {
        "notifyUrl": settings.PAYU_NOTIFY_URL,
        "continueUrl": f"{settings.FRONTEND_URL}/payment/success",
        "customerIp": request.META.get('REMOTE_ADDR', '127.0.0.1'),
        "merchantPosId": settings.PAYU_POS_ID,
        "description": f"Zamówienie zdjęć - {order.id}",
        "currencyCode": "PLN",
        "totalAmount": str(int(order.total_amount * 100)),
        "extOrderId": payu_order_id,
        "products": [
            {
                "name": f"Zdjęcie {photo.title}",
                "unitPrice": str(int(photo.price * 100)),
                "quantity": "1"
            } for photo in order.photos.all()
        ],
        "buyer": {
            "email": request.user.email,
            "firstName": "Nie podano",
            "lastName": "Nie podano",
        }
    }
    
    auth_response = requests.post(
        f"{settings.PAYU_BASE_URL}/pl/standard/user/oauth/authorize",
        data={
            'grant_type': 'client_credentials',
            'client_id': settings.PAYU_CLIENT_ID,
            'client_secret': settings.PAYU_CLIENT_SECRET
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    if auth_response.status_code != 200:
        return Response({"detail": f"Błąd autoryzacji PayU: {auth_response.text}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        token = auth_response.json()['access_token']
    except (ValueError, KeyError):
        return Response({"detail": "Nieprawidłowa odpowiedź autoryzacji PayU"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    order_response = requests.post(
        f"{settings.PAYU_BASE_URL}/api/v2_1/orders",
        json=order_data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        },
        allow_redirects=False
    )
    
    if order_response.status_code != 302:
        return Response({
            "detail": f"Błąd tworzenia zamówienia w PayU: {order_response.text}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        payu_data = order_response.json()
    except ValueError:
        return Response({
            "detail": "Nieprawidłowa odpowiedź JSON od PayU"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if payu_data.get("status", {}).get("statusCode") != "SUCCESS":
        return Response({
            "detail": f"PayU zwróciło błąd: {payu_data}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    redirect_url = payu_data["redirectUri"]
    
    try:
        payu_data = order_response.json()
    except ValueError:
        return Response({"detail": f"Nieprawidłowa odpowiedź zamówienia PayU: {order_response.text}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    redirect_url = payu_data['redirectUri']
    
    return Response({
        "order_id": order.id,
        "payu_order_id": payu_order_id,
        "redirect_url": redirect_url
    })


@api_view(['POST'])
def payu_notify(request):
    data = request.data
    order_id = data.get('extOrderId')
    payu_status = data.get('status')
    
    try:
        order = Order.objects.get(payu_order_id=order_id)
        if payu_status == 'COMPLETED':
            order.status = 'paid'
            from django.utils import timezone
            order.paid_at = timezone.now()
            order.save()
    except Order.DoesNotExist:
        pass
    
    return Response({"status": "OK"})

@api_view(["GET"])
def order_history(request):
    user = request.user
    if not user.is_authenticated:
        return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    
    if user.is_staff:
        orders = Order.objects.all().order_by('-created_at')
    else:
        orders = Order.objects.filter(user=user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

