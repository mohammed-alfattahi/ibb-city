from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy, reverse

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return reverse('admin:index')
        
        # Priority 1: Check for Partner Profile
        if hasattr(user, 'partner_profile'):
            return reverse('partner_dashboard')

        # Priority 2: Check Role
        if hasattr(user, 'role') and user.role:
            role_name = user.role.name.lower()
            if role_name == 'partner':
                return reverse('partner_dashboard')
            elif role_name == 'tourist':
                return reverse('home')
        
        # Default fallback
        return reverse('home')
