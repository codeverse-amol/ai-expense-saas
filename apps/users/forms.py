from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    """Custom authentication form that uses email instead of username."""
    
    class Meta:
        model = User
        fields = ("email", "password")
    
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        # Remove the username field label since we're using email
        self.fields["username"].label = "Email"
        self.fields["username"].widget.attrs.update({
            "placeholder": "Enter your email",
            "class": "form-control"
        })
        self.fields["password"].widget.attrs.update({
            "placeholder": "Enter your password",
            "class": "form-control"
        })
    
    def clean_username(self):
        """Convert username field to email for authentication."""
        username = self.cleaned_data.get("username")
        return username
