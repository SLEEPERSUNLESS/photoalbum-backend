from django.db import models
from django.utils.text import slugify
from django.conf import settings


class Album(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    thumbnail = models.ImageField(upload_to='thumbnails', null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, null=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='albums',
        null=True,
        blank=True,
    )

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
    price = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)

    def __str__(self):
        return self.title


class AlbumAccess(models.Model):
    """Grants access to an album by email address.

    This decouples access from Django User existence; when a user logs in via
    OTP using a matching email, they'll be able to access the album.
    """

    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="accesses")
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("album", "email")
        indexes = [models.Index(fields=["email"])]

    def __str__(self):
        return f"{self.album_id}:{self.email}"


