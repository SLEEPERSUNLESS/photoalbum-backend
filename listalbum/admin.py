from django.contrib import admin
from .models import Photo, Album

# Register your models here.
class AlbumAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title", )}

admin.site.register(Photo)
admin.site.register(Album, AlbumAdmin)