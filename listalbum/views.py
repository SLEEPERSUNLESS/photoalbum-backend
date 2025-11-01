from django.shortcuts import render, get_object_or_404
from django.db import models
from django.utils.text import slugify
from rest_framework.response import Response
from .models import Photo, Album, AlbumAccess
from .serializers import PhotosSerializer, AlbumSerializer
from rest_framework.views import APIView
from rest_framework import generics, mixins, viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .pagination import AlbumPagination
from user_app.models import AllowedEmail


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

