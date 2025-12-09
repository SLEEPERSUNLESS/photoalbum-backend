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
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from user_app import views
from listalbum.views import PhotoAlbumAV, AlbumPhotoListView, order_history, album_access_view, album_access_delete, album_meta_view, album_photo_delete, email_suggestions, create_payment, payu_notify, check_order_status

def health_check(request):
    return JsonResponse({"status": "ok123"}, status=200)

urlpatterns = [
    #path('', include('listalbum.urls')),
    #path('api/auth/', include('user_app.urls')),
    #user_app
    path("api/auth/request_code/", views.request_code, name="request_code"),
    path("api/auth/verify_code/", views.verify_code, name="verify_code"),
    path("api/auth/logout/", views.logout_view, name="logout"),
    path("api/auth/me/", views.me, name="me"),
    path("api/auth/health/", views.health_check, name="health_check"),
    # admin-only endpoints
    path("api/auth/admin/allowed_emails/", views.allowed_emails_view, name="allowed_emails"),
    path("api/auth/admin/allowed_emails/<str:pk>/", views.allowed_email_delete, name="allowed_email_delete"),
    #listalbum
    path('api/albums/', PhotoAlbumAV.as_view(), name='album-list'),
    path('api/albums/<slug:slug>/', AlbumPhotoListView.as_view(), name='album-photos'),
    path('api/albums/<slug:slug>/photos/<uuid:photo_uuid>/', album_photo_delete, name='album-photo-delete'),
    # Admin-only: manage album access by email
    path('api/albums/<slug:slug>/access/', album_access_view, name='album-access'),
    path('api/albums/<slug:slug>/access/<int:pk>/', album_access_delete, name='album-access-delete'),
    path('api/albums/<slug:slug>/meta/', album_meta_view, name='album-meta'),
    path('api/emails/suggest/', email_suggestions, name='email-suggestions'),
    path('api/payment/create/', create_payment, name='create-payment'),
    path('api/payment/notify/', payu_notify, name='payu-notify'),
    path('api/orders/history/', order_history, name='order-history'),
    path('api/orders/<int:order_id>/check-status/', check_order_status, name='check-order-status'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
