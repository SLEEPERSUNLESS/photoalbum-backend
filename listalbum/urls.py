from django.urls import path
from .views import WatchListAV

urlpatterns = [
    path('', WatchListAV.as_view(), name='homepage'),
]