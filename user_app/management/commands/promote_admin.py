from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Promote a user to admin (staff and superuser) by email; auto-creates if missing."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Email address to promote")

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        User = get_user_model()
        user, created = User.objects.get_or_create(email__iexact=email, defaults={"email": email})
        if created:
            user.set_unusable_password()
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        self.stdout.write(self.style.SUCCESS(f"User {email} is now admin (staff+superuser)."))
