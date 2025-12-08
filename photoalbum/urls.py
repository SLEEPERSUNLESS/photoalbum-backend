"""
URL configuration for photoalbum project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from user_app import views
from listalbum.views import PhotoAlbumAV, AlbumPhotoListView, album_access_view, album_access_delete, album_meta_view, album_photo_delete, email_suggestions, create_payment, payu_notify

def health_check(request):
    return JsonResponse({"status": "ok123"}, status=200)

urlpatterns = [
    path('', include('listalbum.urls')),
    #path('api/auth/', include('user_app.urls')),
    #user_app
    path("auth/request_code/", views.request_code, name="request_code"),
    path("auth/verify_code/", views.verify_code, name="verify_code"),
    path("auth/logout/", views.logout_view, name="logout"),
    path("auth/me/", views.me, name="me"),
    path("auth/health/", views.health_check, name="health_check"),
    # admin-only endpoints
    path("auth/admin/allowed_emails/", views.allowed_emails_view, name="allowed_emails"),
    path("auth/admin/allowed_emails/<str:pk>/", views.allowed_email_delete, name="allowed_email_delete"),
    #listalbum
    path('albums/', PhotoAlbumAV.as_view(), name='album-list'),
    path('albums/<slug:slug>/', AlbumPhotoListView.as_view(), name='album-photos'),
    path('albums/<slug:slug>/photos/<int:pk>/', album_photo_delete, name='album-photo-delete'),
    # Admin-only: manage album access by email
    path('albums/<slug:slug>/access/', album_access_view, name='album-access'),
    path('albums/<slug:slug>/access/<int:pk>/', album_access_delete, name='album-access-delete'),
    path('albums/<slug:slug>/meta/', album_meta_view, name='album-meta'),
    path('emails/suggest/', email_suggestions, name='email-suggestions'),
    path('payment/create/', create_payment, name='create-payment'),
    path('payment/notify/', payu_notify, name='payu-notify'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
