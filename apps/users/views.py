from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.contrib.auth import login, authenticate
from django.urls import reverse_lazy
from .forms import SignUpForm


class SignUpView(CreateView):
    """View for user registration."""
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("dashboard")
    
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
