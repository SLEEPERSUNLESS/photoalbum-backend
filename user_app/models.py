from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import random


# Create your models here.
class EmailOTP(models.Model):
	"""One-time codes sent to users' emails for authentication.

	Admin users (is_staff/is_superuser) should continue using the default
	username/password admin flow; this model is intended for normal users.
	"""
	user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="email_otps")
	code = models.CharField(max_length=6)
	created_at = models.DateTimeField(auto_now_add=True)
	expires_at = models.DateTimeField()
	used = models.BooleanField(default=False)

	class Meta:
		indexes = [models.Index(fields=["user", "code"])]

	def is_valid(self):
		return (not self.used) and (self.expires_at > timezone.now())

	@staticmethod
	def generate_code():
		return f"{random.randint(0, 999999):06d}"

