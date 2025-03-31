from django.shortcuts import render
from rest_framework.response import Response
from .models import Photos, Album
from .serializers import PhotosSerializer, AlbumSerializer
from rest_framework.views import APIView


class WatchListAV(APIView):

    def get(self, request):
        albums = Album.objects.all()
        serializer = AlbumSerializer(albums, many=True)
        return Response(serializer.data)
