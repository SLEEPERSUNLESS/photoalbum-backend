from django.contrib import admin
from .models import Photos, Album

# Register your models here.
class AlbumAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title", )}

admin.site.register(Photos)
admin.site.register(Album, AlbumAdmin)