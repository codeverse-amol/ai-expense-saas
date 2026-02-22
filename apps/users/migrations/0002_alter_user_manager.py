# Generated migration to update User manager

from django.db import migrations
from apps.users.models import CustomUserManager


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='User',
            managers=[
                ('objects', CustomUserManager()),
            ],
        ),
    ]
