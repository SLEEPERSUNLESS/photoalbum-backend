from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from .models import Photo, Album
from .serializers import PhotosSerializer, AlbumSerializer
from rest_framework.views import APIView
from rest_framework import generics, mixins, viewsets, status, filters
from .pagination import AlbumPagination


class PhotoAlbumAV(generics.ListAPIView):
    queryset = Album.objects.all().order_by("-created_at")
    pagination_class = AlbumPagination
    serializer_class = AlbumSerializer
    
    

class AlbumPhotoListView(generics.ListAPIView): # allow post here later
    serializer_class = PhotosSerializer

    def get_queryset(self):
        slug = self.kwargs['slug']
        return Photo.objects.filter(album__slug=slug)

#TODO cart model should have photos and users? idk man ask gpt, sprawdz jak to inni robia
# class CartAV(generics.CreateAPIView):
#     serializer_class = PhotosSerializer

#     def get_queryset(self):
#         slug = self.kwargs['slug']
#         return Photo.objects.filter(album__slug=slug)
