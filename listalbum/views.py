from django.shortcuts import render
from rest_framework.response import Response
from .models import Photos
from .serializers import PhotosSerializer
from rest_framework.views import APIView


class WatchListAV(APIView):

    def get(self, request):
        photos = Photos.objects.all()
        serializer = PhotosSerializer(photos, many=True)
        return Response(serializer.data)
