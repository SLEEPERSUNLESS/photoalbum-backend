from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from .models import Photos, Album
from .serializers import PhotosSerializer, AlbumSerializer
from rest_framework.views import APIView
from rest_framework import generics, mixins, viewsets, status, filters
from django_filters.rest_framework import DjangoFilterBackend


class WatchListAV(APIView):

    def get(self, request):
        albums = Album.objects.all()
        serializer = AlbumSerializer(albums, many=True)
        return Response(serializer.data)

class AlbumPhotoListView(generics.ListAPIView):
    serializer_class = PhotosSerializer
    
    def get_queryset(self):  # tutaj dostajemy zdjecia z konkretnego albumu ; nie ma albumu to 404
        album_slug = self.kwargs['slug']
        album = get_object_or_404(Album, slug=album_slug)
        return Photos.objects.filter(album=album)

class ShoppingCartView(APIView):
    def post(self, request):
        # dane z posta z fronta
        selected_photo_ids = request.POST.getlist('selected_photos')
        selected_photos = Photos.objects.filter(id__in=selected_photo_ids)
        return render(request, 'shopping_cart.html', {'photos': selected_photos})


