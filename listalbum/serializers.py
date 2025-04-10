from rest_framework import serializers
from .models import Photo, Album


class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        # exclude = ['created_at']
        fields = ["id", "title", "description", "slug", "photo_count"]


class PhotosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        exclude = ['date_uploaded']
