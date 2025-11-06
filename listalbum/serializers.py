from rest_framework import serializers
from .models import Photo, Album


class AlbumSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)

    class Meta:
        model = Album
        # exclude = ['created_at']
        fields = [
            "id",
            "title",
            "description",
            "thumbnail",
            "slug",
            "photo_count",
            "owner_id",
            "owner_email",
        ]


class PhotosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        exclude = ['date_uploaded']
