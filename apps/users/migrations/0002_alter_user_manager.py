# Generated migration to update User manager

from django.db import migrations


def set_custom_manager(apps, schema_editor):
    """No-op function, just updating the manager definition."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_custom_manager, migrations.RunPython.noop),
    ]

