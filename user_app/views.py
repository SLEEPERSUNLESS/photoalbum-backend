from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
import logging

from .models import EmailOTP

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])
def request_code(request):
	"""Request an email code. Body: {"email": "user@example.com"}

	Creates or reuses an OTP object and emails the code. Returns 200
	whether user existed or not to avoid user enumeration.
	"""
	email = request.data.get("email")
	if not email:
		return Response({"detail": "email required"}, status=status.HTTP_400_BAD_REQUEST)

	User = get_user_model()
	user = None
	try:
		user = User.objects.get(email__iexact=email)
	except User.DoesNotExist:
		# don't reveal existence
		logger.info("OTP requested for non-existent email: %s", email)
		return Response({"detail": "If the email exists you'll receive a code."})

	if user.is_staff or user.is_superuser:
		logger.info("OTP request for admin user: %s", email)

	code = EmailOTP.generate_code()
	expires = timezone.now() + timezone.timedelta(minutes=10)
	otp = EmailOTP.objects.create(user=user, code=code, expires_at=expires)

	# send email (console backend in dev)
	subject = "Your sign-in code"
	message = f"Your sign-in code is: {code}\nIt expires in 10 minutes."
	from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
	try:
		send_mail(subject, message, from_email, [email])
		logger.info("Sent OTP to %s", email)
	except Exception:
		logger.exception("Failed to send OTP to %s", email)

	return Response({"detail": "If the email exists you'll receive a code."})


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
		return Response({"detail": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)

	if user.is_staff or user.is_superuser:
		logger.info("OTP verify for admin user: %s", email)

	try:
		otp = EmailOTP.objects.filter(user=user, code=code, used=False).latest("created_at")
	except EmailOTP.DoesNotExist:
		logger.info("Invalid OTP for %s", email)
		return Response({"detail": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)

	if not otp.is_valid():
		logger.info("Expired or used OTP for %s", email)
		return Response({"detail": "Invalid or expired code"}, status=status.HTTP_400_BAD_REQUEST)

	# mark used
	otp.used = True
	otp.save()

	# create or get token
	token, _ = Token.objects.get_or_create(user=user)
	logger.info("OTP verified for %s, issued token", email)

	return Response({"token": token.key})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
	auth_header = request.META.get('HTTP_AUTHORIZATION', '')
	if auth_header.startswith('Token '):
		token_key = auth_header.split(' ', 1)[1].strip()
		Token.objects.filter(key=token_key, user=request.user).delete()

	else:
		Token.objects.filter(user=request.user).delete()

	logger.info("Logged out user %s", request.user.email)
	return Response(status=status.HTTP_204_NO_CONTENT)

