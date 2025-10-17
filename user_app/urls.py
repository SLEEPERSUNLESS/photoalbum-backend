from django.urls import path
from . import views

urlpatterns = [
    path('rejestracja/', views.register, name='register'),
    path('logowanie/', views.login_view, name='login'),
    path('wylogowanie/', views.logout_view, name='logout'),
]