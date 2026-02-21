from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Test authentication with email and password'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email')
        parser.add_argument('password', type=str, help='User password')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        
        self.stdout.write(f"\nTesting authentication for: {email}")
        self.stdout.write("=" * 50)
        
        # Check if user exists
        try:
            user = User.objects.get(email__iexact=email)
            self.stdout.write(self.style.SUCCESS(f"✓ User found: {user.username}"))
            self.stdout.write(f"  Email: {user.email}")
            self.stdout.write(f"  Active: {user.is_active}")
            self.stdout.write(f"  Is Admin: {user.is_superuser}")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"✗ User NOT found with email: {email}"))
            return
        except User.MultipleObjectsReturned:
            self.stdout.write(self.style.ERROR(f"✗ Multiple users found with email: {email}"))
            return
        
        # Test password
        self.stdout.write(f"\nTesting password...")
        if user.check_password(password):
            self.stdout.write(self.style.SUCCESS("✓ Password is CORRECT"))
        else:
            self.stdout.write(self.style.ERROR("✗ Password is INCORRECT"))
            return
        
        # Test authentication backend
        self.stdout.write(f"\nTesting authentication backend...")
        authenticated_user = authenticate(username=email, password=password)
        
        if authenticated_user is not None:
            self.stdout.write(self.style.SUCCESS(f"✓ Authentication SUCCESSFUL"))
            self.stdout.write(f"  Authenticated as: {authenticated_user.email}")
        else:
            self.stdout.write(self.style.ERROR("✗ Authentication FAILED"))
            self.stdout.write("  (This means the backend rejected the credentials)")
