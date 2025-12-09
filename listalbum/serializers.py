from rest_framework import serializers
from .models import Photo, Album, Order


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
            "access_count",
            "owner_id",
            "owner_email",
        ]


class PhotosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'title', 'url', 'album', 'price', 'uuid']


class OrderSerializer(serializers.ModelSerializer):
    photos = PhotosSerializer(many=True, read_only=True)
    photo_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'photos', 'photo_ids', 'total_amount', 'payu_order_id', 'status', 'created_at', 'paid_at', 'user_email']
        read_only_fields = ['id', 'total_amount', 'payu_order_id', 'status', 'created_at', 'paid_at', 'user_email']

    def create(self, validated_data):
        photo_ids = validated_data.pop('photo_ids')
        user = self.context['request'].user
        photos = Photo.objects.filter(id__in=photo_ids)
        total_amount = sum(photo.price for photo in photos)
        order = Order.objects.create(user=user, total_amount=total_amount, **validated_data)
        order.photos.set(photos)
        return order
