from rest_framework import serializers
from .models import Photo, Album, Order


class AlbumSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Album
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
            "photo_price",
            "full_album_price",
        ]
    
    def get_thumbnail(self, obj):
        """Return the thumbnail URL using our dedicated serve endpoint."""
        if not obj.thumbnail:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/thumbnails/{obj.slug}/')
        return f'/api/thumbnails/{obj.slug}/'


class PhotosSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = Photo
        fields = ['id', 'title', 'url', 'album', 'price', 'uuid']
    
    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/photos/{obj.uuid}/')
        return f'/api/photos/{obj.uuid}/'


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
        photos = Photo.objects.filter(id__in=photo_ids).select_related('album')
        
        # Group photos by album
        album_photos = {}
        for photo in photos:
            album_id = photo.album_id
            if album_id not in album_photos:
                album_photos[album_id] = {
                    'album': photo.album,
                    'photos': [],
                    'total': 0
                }
            album_photos[album_id]['photos'].append(photo)
            album_photos[album_id]['total'] += photo.price
        
        # Calculate total with album discounts
        total_amount = 0
        for album_id, data in album_photos.items():
            album = data['album']
            album_total_photos = album.photos.count()
            order_album_photos = len(data['photos'])
            
            # If all photos from album are in order and album has discount
            if (album_total_photos == order_album_photos and 
                album.full_album_price is not None and 
                album.full_album_price < data['total']):
                total_amount += album.full_album_price
            else:
                total_amount += data['total']
        
        order = Order.objects.create(user=user, total_amount=total_amount, **validated_data)
        order.photos.set(photos)
        return order
