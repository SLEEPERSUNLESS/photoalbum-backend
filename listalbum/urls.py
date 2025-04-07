from django.urls import path
from .views import PhotoAlbumAV, AlbumPhotoListView, ShoppingCartView

urlpatterns = [
    path('albumy/', PhotoAlbumAV.as_view(), name='homepage'),
    path('albumy/<slug:slug>/', AlbumPhotoListView.as_view(), name='album-photos'),
    path('koszyk/', ShoppingCartView.as_view(), name='shopping-cart'),
]