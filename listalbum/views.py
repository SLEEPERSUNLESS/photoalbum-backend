from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from .models import Photo, Album
from .serializers import PhotosSerializer, AlbumSerializer
from rest_framework.views import APIView
from rest_framework import generics, mixins, viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from .pagination import AlbumPagination


class PhotoAlbumAV(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlbumSerializer
    pagination_class = AlbumPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']

    def get_queryset(self):
        # staff users can see everything; regular users see only their albums
        user = self.request.user
        qs = Album.objects.all().order_by("-created_at")
        if user.is_staff:
            return qs
        return qs.filter(owner=user)
    
    

class AlbumPhotoListView(generics.ListAPIView): # allow post here later
    permission_classes = [IsAuthenticated]
    serializer_class = PhotosSerializer

    def get_queryset(self):
        slug = self.kwargs['slug']
        user = self.request.user
        qs = Photo.objects.filter(album__slug=slug)
        # if user is staff they can see photos in any album; otherwise ensure
        # the album belongs to them
        if user.is_staff:
            return qs
        return qs.filter(album__owner=user)

#TODO cart model should have photos and users? idk man ask gpt, sprawdz jak to inni robia
# class CartAV(generics.CreateAPIView):
#     serializer_class = PhotosSerializer

#     def get_queryset(self):
#         slug = self.kwargs['slug']
#         return Photo.objects.filter(album__slug=slug)
