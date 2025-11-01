from django.urls import path
from .views import PhotoAlbumAV, AlbumPhotoListView, album_access_view, album_access_delete, album_meta_view, album_photo_delete, email_suggestions

urlpatterns = [
    path('albums/', PhotoAlbumAV.as_view(), name='album-list'),
    path('albums/<slug:slug>/', AlbumPhotoListView.as_view(), name='album-photos'),
    path('albums/<slug:slug>/photos/<int:pk>/', album_photo_delete, name='album-photo-delete'),
    # Admin-only: manage album access by email
    path('albums/<slug:slug>/access/', album_access_view, name='album-access'),
    path('albums/<slug:slug>/access/<int:pk>/', album_access_delete, name='album-access-delete'),
    path('albums/<slug:slug>/meta/', album_meta_view, name='album-meta'),
    path('emails/suggest/', email_suggestions, name='email-suggestions'),
]