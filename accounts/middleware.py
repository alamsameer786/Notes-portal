from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is trying to access admin without proper permissions
        if request.path.startswith('/admin/') and not request.path.startswith('/admin/login/'):
            if request.user.is_authenticated and not (request.user.is_staff or request.user.is_superuser):
                messages.error(request, 'You do not have permission to access the admin panel.')
                return redirect('student_dashboard')
        
        response = self.get_response(request)
        return response