from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a default superuser for Render deployment'

    def handle(self, *args, **options):
        email = "amol@gmail.com"
        username = "amol3004"
        password = "python@3004"
        
        print("\n" + "=" * 80)
        print("CREATING SUPERUSER")
        print("=" * 80)
        
        # Check if user exists
        user_exists = User.objects.filter(email=email).exists()
        
        if user_exists:
            print(f"✓ User {email} already exists")
            user = User.objects.get(email=email)
            print(f"  Email: {user.email}")
            print(f"  Is Superuser: {user.is_superuser}")
            print(f"  Is Active: {user.is_active}")
            
            # Ensure they have superuser privileges
            if not user.is_superuser or not user.is_staff:
                print("  Upgrading to superuser...")
                user.is_superuser = True
                user.is_staff = True
                user.is_active = True
                user.save()
                print("  ✓ User upgraded to superuser")
            print("=" * 80 + "\n")
            return
        
        # Create new superuser
        print(f"Creating new user: {email}")
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                subscription_plan="premium",
                ai_credits=1000
            )
            print(f"✓ Superuser created successfully!")
            print(f"  Email: {user.email}")
            print(f"  Username: {user.username}")
            print(f"  Is Superuser: {user.is_superuser}")
            print(f"  Is Active: {user.is_active}")
            print(f"\n✓ Login with:")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
        except Exception as e:
            print(f"✗ Error creating superuser: {e}")
            import traceback
            traceback.print_exc()
        
        print("=" * 80 + "\n")


