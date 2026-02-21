from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import sys

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a default superuser for Render deployment'

    def handle(self, *args, **options):
        email = "amol@gmail.com"
        username = "amol3004"
        password = "python@3004"
        
        self.stdout.write("=" * 60)
        self.stdout.write("Creating/Checking superuser...")
        self.stdout.write("=" * 60)
        
        # Check if user already exists
        try:
            user = User.objects.get(email=email)
            self.stdout.write(
                self.style.SUCCESS(f'✓ User with email {email} already exists!')
            )
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Is Superuser: {user.is_superuser}')
            self.stdout.write(f'  Is Active: {user.is_active}')
            
            # Make sure they're a superuser
            if not user.is_superuser:
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS('✓ Updated to superuser'))
            
            self.stdout.write("=" * 60)
            return
        except User.DoesNotExist:
            pass
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error checking user: {e}'))
            sys.exit(1)
        
        # Create superuser
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                subscription_plan="premium",
                ai_credits=1000
            )
            self.stdout.write(self.style.SUCCESS('✓ Superuser created successfully!'))
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Is Superuser: {user.is_superuser}')
            self.stdout.write(f'  Is Active: {user.is_active}')
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS('✓ You can now login with:'))
            self.stdout.write(f'  Email: {email}')
            self.stdout.write(f'  Password: {password}')
            self.stdout.write("=" * 60)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error creating superuser: {e}'))
            import traceback
            traceback.print_exc()
            sys.exit(1)
