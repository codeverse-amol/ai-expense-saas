from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailAuthenticationBackend(ModelBackend):
    """Custom authentication backend that allows users to login with email."""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to get user by email
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None
        
        if password and user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
