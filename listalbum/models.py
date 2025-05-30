from django.db import models
from django.utils.text import slugify


class Album(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    thumbnail = models.ImageField(upload_to='thumbnails', null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, null=False)
    # slug to nazwa zmiennej w django -> ten slug bedzie generowal dynamiczny url.
    # mamy album o nazwie przedszkole-3 to stworzy url /przedszkole-3

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def photo_count(self):
        return self.photos.count()

class Photo(models.Model):
    title = models.CharField(max_length=255)
    url = models.ImageField(upload_to='photos', null=True, blank=True)
    album = models.ForeignKey(
        Album, on_delete=models.CASCADE, related_name='photos')
    date_uploaded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


