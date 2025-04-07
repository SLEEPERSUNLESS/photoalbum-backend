from rest_framework import serializers
from .models import Photos, Album

class PhotosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photos
        exclude = ['created_at', 'image']
        
class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        exclude = ['slug', 'created_at']