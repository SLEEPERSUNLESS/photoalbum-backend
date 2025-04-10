from django.urls import path
from .views import PhotoAlbumAV, AlbumPhotoListView

urlpatterns = [
    path('albums/', PhotoAlbumAV.as_view(), name='album-list'),
    path('albums/<slug:slug>/', AlbumPhotoListView.as_view(), name='album-photos'),
]