from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
import uuid


class CustomUserManager(UserManager):
    """Custom user manager for email-based authentication."""
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if not email:
            raise ValueError('Email must be set')
        
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True)

    # Future SaaS fields
    subscription_plan = models.CharField(max_length=50, default="free")
    ai_credits = models.IntegerField(default=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    
    objects = CustomUserManager()

    def __str__(self):
        return self.email