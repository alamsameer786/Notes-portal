from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('admin', 'Admin'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # Only set is_staff for regular users, not superusers
        if not self.is_superuser:
            if self.user_type == 'admin':
                self.is_staff = True
            else:
                self.is_staff = False
        # For superusers, keep is_staff=True always
        elif self.is_superuser:
            self.is_staff = True
            self.is_approved = True  # Superusers should always be approved
            
        super().save(*args, **kwargs)
    
    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?"""
        if self.is_staff or self.is_superuser:
            return True
        return super().has_perm(perm, obj)
    
    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?"""
        if self.is_staff or self.is_superuser:
            return True
        return super().has_module_perms(app_label)
    
    class Meta:
        swappable = 'AUTH_USER_MODEL'

    def __str__(self):
        return self.username

class AccessRequest(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    reason = models.TextField()
    is_processed = models.BooleanField(default=False)
    processed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Access Request'
        verbose_name_plural = 'Access Requests'
    
    def __str__(self):
        return f"{self.name} - {self.email} ({'Processed' if self.is_processed else 'Pending'})"
