from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a default superuser for Render deployment'

    def handle(self, *args, **options):
        email = "amol@gmail.com"
        username = "amol3004"
        password = "python@3004"
        
        print("\n" + "=" * 80)
        print("SUPERUSER CREATION")
        print("=" * 80 + "\n")
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
            print(f"✓ User {email} already exists")
            
            # Ensure they have full superuser privileges
            needs_update = False
            if not user.is_superuser:
                user.is_superuser = True
                needs_update = True
            if not user.is_staff:
                user.is_staff = True
                needs_update = True
            if not user.is_active:
                user.is_active = True
                needs_update = True
            
            if needs_update:
                user.save()
                print(f"✓ User updated with superuser privileges\n")
            else:
                print(f"✓ User already has full privileges\n")
                
        except User.DoesNotExist:
            print(f"Creating superuser: {email}")
            
            # Create user manually to avoid manager issues
            try:
                user = User.objects.create(
                    username=username,
                    email=email,
                    is_superuser=True,
                    is_staff=True,
                    is_active=True,
                    subscription_plan="premium",
                    ai_credits=1000
                )
                user.set_password(password)
                user.save()
                
                print(f"✓ User created successfully!")
                print(f"  Email: {user.email}")
                print(f"  Username: {user.username}")
                print(f"  Is Superuser: {user.is_superuser}")
                print(f"  Is Staff: {user.is_staff}")
                print(f"  Is Active: {user.is_active}\n")
                print(f"✓ You can login with:")
                print(f"  Email: {email}")
                print(f"  Password: {password}\n")
                
            except Exception as e:
                print(f"✗ Error creating user: {e}")
                import traceback
                traceback.print_exc()
        
        print("=" * 80 + "\n")



