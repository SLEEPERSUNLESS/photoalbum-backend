from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, status
from .models import Photos, Album
from .serializers import PhotosSerializer, AlbumSerializer


class PhotoAlbumsAV(APIView):
    #wyswietlanie wszystkich albumów    ->   dodac paginacje
    
    def get(self, request, format=None):
        albums = Album.objects.all()
        
        # Check if this is an API request or a template request
        if request.accepted_renderer.format == 'json' or format == 'json':
            # API response
            serializer = AlbumSerializer(albums, many=True)
            return Response(serializer.data)
        else:
            # Template response
            # Get cart count for the cart badge
            cart_count = len(request.session.get('cart', []))
            
            return render(request, 'listalbum/albums_list.html', {
                'albums': albums,
                'cart_count': cart_count
            })


class AlbumPhotoListView(generics.ListAPIView):
    # wyswietlanie wszystkich zdjęć w albumie
    # dodac paginacje?
    # mozna dodawac do koszyka
    
    serializer_class = PhotosSerializer
    
    def get(self, request, *args, **kwargs):    # wyswietlanie zdjec w albumie i renderuje template
        album_slug = self.kwargs['slug']
        album = get_object_or_404(Album, slug=album_slug)
        photos = Photos.objects.filter(album=album)
        return render(request, 'listalbum/album_photo_list.html', {
            'photos': photos, 
            'album': album
        })

    def post(self, request, *args, **kwargs):   # dodawanie zdjec do koszyka
        album_slug = self.kwargs['slug']
        album = get_object_or_404(Album, slug=album_slug)
        
        selected_photo_ids = request.POST.getlist('selected_photos')
        
        if not selected_photo_ids:
            messages.warning(request, "No photos were selected.")
            return redirect('album-photo-list', slug=album_slug)
        
        # stringi dla sesji
        selected_photo_ids = [str(id) for id in selected_photo_ids]
        
        # inicjalizacja koszyka
        if 'cart' not in request.session:
            request.session['cart'] = []
        
        # zlapanie koszyka i dodanie zdjec
        cart = request.session.get('cart', [])
        cart.extend(selected_photo_ids)
        
        # usuwanie duplikatów
        unique_cart = []
        for item in cart:
            if item not in unique_cart:
                unique_cart.append(item)
                
        request.session['cart'] = unique_cart
        request.session.modified = True  # Ensure session is saved
        
        messages.success(request, f"{len(selected_photo_ids)} photo(s) added to cart successfully.")
        return redirect('shopping-cart')


class ShoppingCartView(APIView):
    # wyswietlanie zdjec w koszyku
    
    def get(self, request):   # wyswietlanie zdjec w koszyku
        cart = request.session.get('cart', [])
        photos_in_cart = Photos.objects.filter(id__in=cart)
        
        # orderowanie itemow w koszyku
        ordered_photos = []
        for photo_id in cart:
            for photo in photos_in_cart:
                if str(photo.id) == str(photo_id):
                    ordered_photos.append(photo)
                    break
        # renderuje template
        return render(request, 'listalbum/shopping_cart.html', {
            'photos': ordered_photos
        })
    
    def post(self, request):
        # usuwanie itemow z koszyka
        action = request.POST.get('action')
        
        if action == 'clear':
            # wyczyszczanie koszyka calego
            if 'cart' in request.session:
                del request.session['cart']
                request.session.modified = True
            messages.success(request, "Your cart has been cleared.")
            
        elif action == 'remove':
            #usuwanie z koszyka
            photo_id = request.POST.get('photo_id')
            if photo_id and 'cart' in request.session:
                cart = request.session.get('cart', [])
                if photo_id in cart:
                    cart.remove(photo_id)
                    request.session['cart'] = cart
                    request.session.modified = True
                    messages.success(request, "Photo removed from cart.")
        
        return redirect('shopping-cart')
