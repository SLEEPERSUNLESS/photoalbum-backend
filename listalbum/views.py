from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from .models import Photo, Album
from .serializers import PhotosSerializer, AlbumSerializer
from rest_framework.views import APIView
from rest_framework import generics, mixins, viewsets, status, filters


class PhotoAlbumAV(APIView):

    def get(self, request):
        albums = Album.objects.all()
        serializer = AlbumSerializer(albums, many=True)
        return Response(serializer.data)

class AlbumPhotoListView(generics.RetrieveAPIView):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    lookup_field = 'slug'  # Make sure it's 'slug', not 'id'


class ShoppingCartView(APIView):
    def post(self, request):
        # dane z posta z fronta // tu jeszcze nic nie dziala TODO
        selected_photo_ids = request.POST.getlist('selected_photos')
        selected_photos = Photo.objects.filter(id__in=selected_photo_ids)
        return render(request, 'shopping_cart.html', {'photos': selected_photos})


