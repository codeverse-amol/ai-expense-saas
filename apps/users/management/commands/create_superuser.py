from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError, IntegrityError
import traceback

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a default superuser for Render deployment'

    def handle(self, *args, **options):
        email = "amol@gmail.com"
        username = "amol3004"
        password = "python@3004"
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("SUPERUSER CREATION - DETAILED LOG")
        self.stdout.write("=" * 80)
        
        # Check if database is available
        try:
            self.stdout.write("[1/4] Checking database connection...")
            User.objects.all().exists()
            self.stdout.write("      ✓ Database is available\n")
        except OperationalError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'      ✗ Database not available: {e}\n'
                    f'      Skipping superuser creation.\n'
                )
            )
            self.stdout.write("=" * 80 + "\n")
            return
        
        # Check if user already exists
        self.stdout.write("[2/4] Checking if user exists...")
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f"      ✓ User found with email: {email}\n")
            self.stdout.write(f"[3/4] User details:")
            self.stdout.write(f"      - Username: {user.username}")
            self.stdout.write(f"      - Is Superuser: {user.is_superuser}")
            self.stdout.write(f"      - Is Active: {user.is_active}\n")
            
            # Make sure they're a superuser and active
            updated = False
            if not user.is_superuser or not user.is_staff or not user.is_active:
                self.stdout.write("[4/4] Updating user to superuser with full permissions...")
                user.is_superuser = True
                user.is_staff = True
                user.is_active = True
                user.subscription_plan = "premium"
                user.ai_credits = 1000
                user.save()
                updated = True
                self.stdout.write("      ✓ User updated successfully\n")
            else:
                self.stdout.write("[4/4] User is already a superuser with full permissions\n")
            
            self.stdout.write(self.style.SUCCESS("✓ SUPERUSER READY FOR LOGIN"))
            self.stdout.write(f"  Email: {email}")
            self.stdout.write(f"  Password: {password}\n")
            
        except User.DoesNotExist:
            self.stdout.write("      ✗ User does not exist, creating new user...\n")
            
            # Create the superuser
            self.stdout.write("[3/4] Creating superuser...")
            try:
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    subscription_plan="premium",
                    ai_credits=1000
                )
                self.stdout.write("      ✓ Superuser created successfully\n")
                
                self.stdout.write("[4/4] Verifying user in database...")
                # Verify the user was actually created
                verify_user = User.objects.get(email=email)
                self.stdout.write(f"      ✓ User verified in database\n")
                self.stdout.write(f"      - Email: {verify_user.email}")
                self.stdout.write(f"      - Username: {verify_user.username}")
                self.stdout.write(f"      - Is Superuser: {verify_user.is_superuser}")
                self.stdout.write(f"      - Is Active: {verify_user.is_active}\n")
                
                self.stdout.write(self.style.SUCCESS("✓ SUPERUSER CREATED SUCCESSFULLY"))
                self.stdout.write(f"  Email: {email}")
                self.stdout.write(f"  Password: {password}\n")
                
            except IntegrityError as e:
                self.stdout.write(
                    self.style.ERROR(f"      ✗ IntegrityError (user may already exist): {e}\n")
                )
                self.stdout.write("        Attempting to update existing user...\n")
                try:
                    user = User.objects.get(email=email)
                    user.set_password(password)
                    user.is_superuser = True
                    user.is_staff = True
                    user.is_active = True
                    user.subscription_plan = "premium"
                    user.ai_credits = 1000
                    user.save()
                    self.stdout.write(self.style.SUCCESS("        ✓ User updated successfully\n"))
                except Exception as e2:
                    self.stdout.write(self.style.ERROR(f"        ✗ Failed to update: {e2}\n"))
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"      ✗ Error creating superuser: {e}\n")
                )
                self.stdout.write(f"      Traceback: {traceback.format_exc()}\n")
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Unexpected error: {e}\n")
            )
            self.stdout.write(f"Traceback: {traceback.format_exc()}\n")
        
        self.stdout.write("=" * 80 + "\n")

