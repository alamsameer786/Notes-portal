from django.core.management.base import BaseCommand
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Fix user permissions for admin access'
    
    def handle(self, *args, **options):
        # Ensure all superusers are also marked as admin type
        superusers = CustomUser.objects.filter(is_superuser=True)
        for user in superusers:
            if user.user_type != 'admin':
                user.user_type = 'admin'
                user.save()
                self.stdout.write(f"Updated {user.username} to admin type")
        
        # Ensure all admin users have is_staff functionality
        admins = CustomUser.objects.filter(user_type='admin')
        for user in admins:
            if not user.is_approved:
                user.is_approved = True
                user.save()
                self.stdout.write(f"Approved admin user {user.username}")
        
        self.stdout.write(self.style.SUCCESS("User permissions fixed successfully"))