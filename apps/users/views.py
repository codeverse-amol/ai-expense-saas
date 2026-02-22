from django.shortcuts import render, redirect
from django.views.generic import CreateView, View
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import SignUpForm, EmailAuthenticationForm


class LoginView(View):
    """Custom login view with email authentication."""
    template_name = "registration/login.html"
    form_class = EmailAuthenticationForm
    
    def get(self, request):
        """Display login form."""
        # Redirect authenticated users to dashboard
        if request.user.is_authenticated:
            return redirect('dashboard')
        
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        """Handle login form submission."""
        # Redirect authenticated users to dashboard
        if request.user.is_authenticated:
            return redirect('dashboard')
        
        form = self.form_class(request, data=request.POST)
        
        if form.is_valid():
            login(request, form.get_user(), backend='apps.users.backends.EmailAuthenticationBackend')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        
        return render(request, self.template_name, {'form': form})


class SignUpView(CreateView):
    """View for user registration."""
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")
    
    def dispatch(self, request, *args, **kwargs):
        """If user is already authenticated, redirect to dashboard."""
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Save the user and show success message."""
        user = form.save()
        
        # Add success message
        messages.success(
            self.request,
            'Account created successfully! Please login with your credentials.'
        )
        
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
