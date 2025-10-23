from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import random


# Create your models here.
class EmailOTP(models.Model):
    
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


class AllowedEmail(models.Model):

	email = models.EmailField(unique=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(
		get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name="allowed_emails_created"
	)

	class Meta:
		ordering = ["-created_at"]
		indexes = [models.Index(fields=["email"]) ]

	def __str__(self):
		return self.email

