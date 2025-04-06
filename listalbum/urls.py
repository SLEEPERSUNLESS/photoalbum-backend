from django.urls import path
from . import views

urlpatterns = [
    path('albumy/', views.PhotoAlbumsAV.as_view(), name='albums'),
    path('albumy/<slug:slug>/photos/', views.AlbumPhotoListView.as_view(), name='album-photo-list'),
    path('koszyk/', views.ShoppingCartView.as_view(), name='shopping-cart'),
]