from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Check all users in the database'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("CHECKING USERS IN DATABASE")
        self.stdout.write("=" * 80)
        
        try:
            user_count = User.objects.count()
            self.stdout.write(f"\nTotal users in database: {user_count}")
            
            if user_count == 0:
                self.stdout.write(self.style.WARNING("\n⚠️  NO USERS FOUND IN DATABASE!\n"))
            else:
                self.stdout.write("\nUsers:\n")
                for user in User.objects.all():
                    self.stdout.write(f"  • Email: {user.email}")
                    self.stdout.write(f"    Username: {user.username}")
                    self.stdout.write(f"    Is Active: {user.is_active}")
                    self.stdout.write(f"    Is Superuser: {user.is_superuser}")
                    self.stdout.write(f"    Created: {user.created_at}")
                    self.stdout.write("")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Error: {e}\n"))
        
        self.stdout.write("=" * 80)
