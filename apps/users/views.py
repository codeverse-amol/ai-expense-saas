from django.shortcuts import render, redirect
from django.views.generic import CreateView, View
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.urls import reverse_lazy
from .forms import SignUpForm, EmailAuthenticationForm


class CustomLoginView(DjangoLoginView):
    """Custom login view with email authentication."""
    form_class = EmailAuthenticationForm
    template_name = "registration/login.html"
    
    def dispatch(self, request, *args, **kwargs):
        """If user is already authenticated, redirect to dashboard."""
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class SignUpView(CreateView):
    """View for user registration."""
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("dashboard")
    
    def dispatch(self, request, *args, **kwargs):
        """If user is already authenticated, redirect to dashboard."""
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Save the user and log them in."""
        user = form.save()
        
        # Authenticate and login the user
        login(self.request, user, backend='apps.users.backends.EmailAuthenticationBackend')
        
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Account'
        return context


class LogoutView(View):
    """Custom logout view."""
    
    def post(self, request):
        """Handle POST logout request."""
        logout(request)
        return redirect('login')
    
    def get(self, request):
        """Handle GET logout request."""
        logout(request)
        return redirect('login')
