#!/usr/bin/env python
"""
Script to create a superuser on Render or any production environment.
Run this after deploying to production.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
sys.path.insert(0, str(Path(__file__).resolve().parent))

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_superuser():
    """Create a superuser with predefined credentials."""
    
    email = "amol@gmail.com"
    username = "amol3004"
    password = "python@3004"
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        print(f"✓ User with email {email} already exists!")
        user = User.objects.get(email=email)
        print(f"  Username: {user.username}")
        print(f"  Is Superuser: {user.is_superuser}")
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
        print(f"✓ Superuser created successfully!")
        print(f"  Email: {user.email}")
        print(f"  Username: {user.username}")
        print(f"  Is Superuser: {user.is_superuser}")
        print(f"\n✓ You can now login with:")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
    except Exception as e:
        print(f"✗ Error creating superuser: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_superuser()
