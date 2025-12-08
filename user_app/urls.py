from django.urls import path
from . import views

urlpatterns = [
    #path("request_code/", views.request_code, name="request_code"),
    path("verify_code/", views.verify_code, name="verify_code"),
    path("logout/", views.logout_view, name="logout"),
    path("me/", views.me, name="me"),
    path("health/", views.health_check, name="health_check"),
    # admin-only endpoints
    path("admin/allowed_emails/", views.allowed_emails_view, name="allowed_emails"),
    path("admin/allowed_emails/<str:pk>/", views.allowed_email_delete, name="allowed_email_delete"),
]
