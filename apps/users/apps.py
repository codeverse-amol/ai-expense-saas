from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'apps.users'    
    def ready(self):
        """Create default superuser when app is ready (on startup)."""
        from django.contrib.auth import get_user_model
        from django.db.utils import OperationalError
        
        User = get_user_model()
        email = "amol@gmail.com"
        username = "amol3004"
        password = "python@3004"
        
        try:
            # Check if database is available
            User.objects.exists()
            
            # Check if user exists
            if not User.objects.filter(email=email).exists():
                # Create the superuser
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
                print(f"✓ Superuser created: {email}")
            else:
                # Ensure user has correct permissions
                user = User.objects.get(email=email)
                updated = False
                if not user.is_superuser or not user.is_staff or not user.is_active:
                    user.is_superuser = True
                    user.is_staff = True
                    user.is_active = True
                    user.save()
                    updated = True
                    print(f"✓ User upgraded to superuser: {email}")
        except OperationalError:
            # Database not ready yet, will try on next startup
            pass
        except Exception as e:
            # Silently catch other errors to not break app startup
            print(f"Note: Could not ensure superuser exists: {e}")