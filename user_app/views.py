from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
import logging
import re
from django.db.models import Q

from .models import EmailOTP, AllowedEmail

logger = logging.getLogger(__name__)

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def ensure_user_and_allowed_email(email: str, created_by=None) -> tuple:
	"""
	Ensure that an AllowedEmail and User exist for the given email.
	Creates them if they don't exist.
	
	Args:
		email: The email address to ensure exists
		created_by: The user who is creating this entry (optional)
	
	Returns:
		tuple: (allowed_email_obj, user_obj, was_created)
	"""
	email = email.strip().lower()
	User = get_user_model()
	
	# Create or get AllowedEmail
	allowed_obj, allowed_created = AllowedEmail.objects.get_or_create(
		email=email,
		defaults={"created_by": created_by}
	)
	
	# Reactivate if it was deactivated
	if not allowed_created and not allowed_obj.is_active:
		allowed_obj.is_active = True
		allowed_obj.save(update_fields=["is_active"])
	
	# Create User if doesn't exist
	user = None
	user_created = False
	try:
		user = User.objects.get(email__iexact=email)
	except User.DoesNotExist:
		user = User.objects.create(email=email)
		try:
			user.set_unusable_password()
			user.save(update_fields=["password"])
		except Exception:
			pass
		user_created = True
	
	return allowed_obj, user, allowed_created or user_created


@api_view(["POST"])
@permission_classes([AllowAny])
def request_code(request):
	"""Request an email code. Body: {"email": "user@example.com"}
	"""
	email = request.data.get("email")
	if not email:
		return Response({"detail": "email required"}, status=status.HTTP_400_BAD_REQUEST)

	User = get_user_model()
	user = None
	try:
		user = User.objects.get(email__iexact=email)
	except User.DoesNotExist:
		user = None

	if user and (user.is_staff or user.is_superuser):
		pass
	else:
		allow = AllowedEmail.objects.filter(email__iexact=email, is_active=True).first()
		if not allow:
			logger.info("OTP requested for non-allowed email: %s", email)
			return Response({
				"detail": "Ten adres e-mail nie jest przypisany do żadnego albumu. Skontaktuj się z fotografem."
			}, status=status.HTTP_403_FORBIDDEN)
		if not user:
			user = User.objects.create(email=email)
			try:
				user.set_unusable_password()
				user.save(update_fields=["password"])
			except Exception:
				pass

	if user.is_staff or user.is_superuser:
		logger.info("OTP request for admin user: %s", email)

	code = EmailOTP.generate_code()
	expires = timezone.now() + timezone.timedelta(minutes=10)
	otp = EmailOTP.objects.create(user=user, code=code, expires_at=expires)

	subject = "Your sign-in code"
	message = f"Your sign-in code is: {code}\nIt expires in 10 minutes."
	from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
	try:
		send_mail(subject, message, from_email, [email])
		logger.info("Sent OTP to %s", email)
	except Exception:
		logger.exception("Failed to send OTP to %s", email)

	return Response({"detail": "Kod został wysłany na podany e-mail (jeśli istnieje)."})


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_code(request):
	"""Verify code and return an auth token. Body: {"email":"...","code":"123456"} """
	email = request.data.get("email")
	code = request.data.get("code")
	if not email or not code:
		return Response({"detail": "email and code required"}, status=status.HTTP_400_BAD_REQUEST)

	User = get_user_model()
	try:
		user = User.objects.get(email__iexact=email)
	except User.DoesNotExist:
		logger.info("OTP verify for non-existent email: %s", email)
		return Response({"detail": "Niepoprawny kod"}, status=status.HTTP_400_BAD_REQUEST)

	if user.is_staff or user.is_superuser:
		logger.info("OTP verify for admin user: %s", email)

	try:
		otp = EmailOTP.objects.filter(user=user, code=code, used=False).latest("created_at")
	except EmailOTP.DoesNotExist:
		logger.info("Invalid OTP for %s", email)
		return Response({"detail": "Niepoprawny kod"}, status=status.HTTP_400_BAD_REQUEST)

	if not otp.is_valid():
		logger.info("Expired or used OTP for %s", email)
		return Response({"detail": "Niepoprawny lub przeterminowany kod"}, status=status.HTTP_400_BAD_REQUEST)

	otp.used = True
	otp.save()

	refresh = RefreshToken.for_user(user)
	logger.info("OTP verified for %s, issued JWT tokens", email)

	return Response({"access": str(refresh.access_token), "refresh": str(refresh)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
	logger.info("Logged out user %s", request.user.email)
	return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])    
@permission_classes([IsAuthenticated])
def me(request):
	"""Return basic info about current user."""
	u = request.user
	return Response({
		"id": u.id,
		"email": getattr(u, "email", None),
		"is_staff": bool(getattr(u, "is_staff", False)),
		"is_superuser": bool(getattr(u, "is_superuser", False)),
	})


# ------- Admin-only endpoints to manage Allowed Emails -------

@api_view(["GET", "POST"])  
@permission_classes([IsAuthenticated, IsAdminUser])
def allowed_emails_view(request):
	if request.method == "GET":
		items = AllowedEmail.objects.all()
		allowed = [
			{"id": it.id, "email": it.email, "is_active": it.is_active, "created_at": it.created_at, "type": "allowed", "is_admin": False}
			for it in items
		]
		User = get_user_model()
		admins_qs = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).distinct()
		admins = [
			{"id": f"admin-{u.id}", "email": getattr(u, 'email', ''), "created_at": getattr(u, 'date_joined', None), "type": "admin", "is_admin": True}
			for u in admins_qs
		]
		return Response(allowed + admins)
	# POST
	email = request.data.get("email")
	if not email:
		return Response({"detail": "email required"}, status=status.HTTP_400_BAD_REQUEST)
	is_admin = request.data.get("is_admin", False)
	User = get_user_model()
	if is_admin:
		# Create or promote to admin
		user, created = User.objects.get_or_create(email__iexact=email, defaults={"email": email})
		if created:
			user.set_unusable_password()
		user.is_staff = True
		user.is_superuser = True
		user.save()
		return Response({"id": f"admin-{user.id}", "email": user.email, "type": "admin", "is_admin": True}, status=status.HTTP_201_CREATED)
	else:
		# Create allowed email
		obj, created = AllowedEmail.objects.get_or_create(email=email.lower(), defaults={"created_by": request.user})
		if not created:
			if not obj.is_active:
				obj.is_active = True
				obj.save(update_fields=["is_active"])
		if not User.objects.filter(email__iexact=email).exists():
			user = User.objects.create(email=email)
			try:
				user.set_unusable_password()
				user.save(update_fields=["password"])
			except Exception:
				pass
		return Response({"id": obj.id, "email": obj.email, "is_active": obj.is_active}, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])  
@permission_classes([IsAuthenticated, IsAdminUser])
def allowed_email_delete(request, pk: str):
	User = get_user_model()
	if pk.startswith("admin-"):
		try:
			user_id = int(pk.split("-")[1])
			user = User.objects.get(pk=user_id)
		except (ValueError, User.DoesNotExist):
			return Response({"detail": "Invalid admin id"}, status=status.HTTP_400_BAD_REQUEST)
		user.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)
	else:
		try:
			obj = AllowedEmail.objects.get(pk=int(pk))
		except (ValueError, AllowedEmail.DoesNotExist):
			return Response(status=status.HTTP_204_NO_CONTENT)
		obj.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
	"""Return basic server information."""
	return Response({
		"status": "ok",
		"server": "PhotoAlbum Backend",
		"version": "1.0",
		"timestamp": timezone.now().isoformat()
	})

