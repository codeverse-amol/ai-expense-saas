from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a default superuser for Render deployment'

    def handle(self, *args, **options):
        email = "amol@gmail.com"
        username = "amol3004"
        password = "python@3004"
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            self.stdout.write(
                self.style.SUCCESS(f'✓ User with email {email} already exists!')
            )
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Is Superuser: {user.is_superuser}')
            return
        
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
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ You can now login with:')
            )
            self.stdout.write(f'  Email: {email}')
            self.stdout.write(f'  Password: {password}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error creating superuser: {e}'))
