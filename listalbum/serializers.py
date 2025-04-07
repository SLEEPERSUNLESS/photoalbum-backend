from rest_framework import serializers
from .models import Photo, Album

class PhotosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        exclude = ['date_uploaded']
        
class AlbumSerializer(serializers.ModelSerializer):
    photos = PhotosSerializer(many=True)
    class Meta:
        model = Album
        exclude = ['created_at']