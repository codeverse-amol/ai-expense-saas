from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailAuthenticationBackend(ModelBackend):
    """Custom authentication backend that allows users to login with email."""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            logger.warning(f"[AUTH] Missing credentials - username: {bool(username)}, password: {bool(password)}")
            return None
        
        logger.info(f"[AUTH] Attempting to authenticate with email: {username}")
        
        try:
            # Try to get user by email (case-insensitive)
            user = User.objects.get(email__iexact=username)
            logger.info(f"[AUTH] User found with email: {user.email}")
            logger.info(f"[AUTH] User is_active: {user.is_active}")
        except User.DoesNotExist:
            logger.warning(f"[AUTH] User NOT found with email: {username}")
            # Run the default password hasher once to reduce timing differences
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            logger.error(f"[AUTH] Multiple users found with email: {username}")
            user = User.objects.filter(email__iexact=username).first()
            if not user:
                return None
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"[AUTH] User is inactive: {user.email}")
            return None
        
        # Check password
        if user.check_password(password):
            logger.info(f"[AUTH] ✓ Authentication SUCCESSFUL for: {user.email}")
            return user
        else:
            logger.warning(f"[AUTH] ✗ Invalid password for user: {user.email}")
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
