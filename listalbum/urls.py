from django.urls import path
from .views import WatchListAV, AlbumPhotoListView, ShoppingCartView

urlpatterns = [
    path('', WatchListAV.as_view(), name='homepage'),
    path('albumy/<slug:slug>/', AlbumPhotoListView.as_view(), name='album-photos'),
    path('koszyk/', ShoppingCartView.as_view(), name='shopping-cart'),
]