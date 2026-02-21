from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'List all users and their email addresses'

    def handle(self, *args, **options):
        users = User.objects.all()
        
        if not users.exists():
            self.stdout.write(self.style.WARNING('No users found in database'))
            return
        
        self.stdout.write(self.style.SUCCESS('=== Users in Database ===\n'))
        
        for user in users:
            status = "✓ ACTIVE" if user.is_active else "✗ INACTIVE"
            admin = "(Admin)" if user.is_superuser else ""
            
            self.stdout.write(
                f"ID: {user.pk}\n"
                f"  Email: {user.email}\n"
                f"  Username: {user.username}\n"
                f"  Status: {status} {admin}\n"
                f"  Created: {user.date_joined}\n"
            )
