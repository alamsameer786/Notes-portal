from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
import re
from .models import CustomUser, AccessRequest
import secrets


class UserTypeFilter(admin.SimpleListFilter):
    title = 'user type'
    parameter_name = 'user_type'

    def lookups(self, request, model_admin):
        return (
            ('admin', 'Admins'),
            ('student', 'Students'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'admin':
            return queryset.filter(user_type='admin')
        if self.value() == 'student':
            return queryset.filter(user_type='student')


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_approved', 'is_staff', 'is_superuser', 'date_joined')
    list_filter = (UserTypeFilter, 'is_approved', 'is_staff', 'is_superuser', 'date_joined')
    actions = ['approve_users', 'disapprove_users', 'make_admin', 'make_student']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'avatar', 'is_approved')}),
    )
    
    def approve_users(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, "Selected users have been approved.")
    approve_users.short_description = "Approve selected users"
    
    def disapprove_users(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, "Selected users have been disapproved.")
    disapprove_users.short_description = "Disapprove selected users"
    
    def make_admin(self, request, queryset):
        queryset.update(user_type='admin', is_staff=True)
        self.message_user(request, "Selected users have been made admins.")
    make_admin.short_description = "Make selected users admins"
    
    def make_student(self, request, queryset):
        queryset.update(user_type='student', is_staff=False)
        self.message_user(request, "Selected users have been made students.")
    make_student.short_description = "Make selected users students"


@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    # FIXED: Changed 'requested_at' to 'created_at' to match the model
    list_display = ('name', 'email', 'created_at', 'is_processed', 'processed_by', 'action_buttons')
    list_filter = ('is_processed', 'created_at')
    readonly_fields = ('name', 'email', 'reason', 'created_at', 'processed_at')
    actions = ['mark_as_processed', 'mark_as_pending']
    search_fields = ('name', 'email')
    ordering = ('-created_at',)
    
    # ENHANCED: Better fieldsets organization
    fieldsets = (
        ('Request Information', {
            'fields': ('name', 'email', 'reason', 'created_at')
        }),
        ('Processing Status', {
            'fields': ('is_processed', 'processed_by', 'processed_at')
        }),
    )
    
    def action_buttons(self, obj):
        if not obj.is_processed:
            return format_html(
                '<a class="button" href="{}">Create User</a>&nbsp;'
                '<a class="button" href="{}" onclick="return confirm(\'Are you sure?\')">Reject</a>',
                f'/admin/accounts/accessrequest/{obj.id}/create_user/',
                f'/admin/accounts/accessrequest/{obj.id}/reject_request/'
            )
        return format_html(
            '<span style="color: green;">✓ Processed by {}</span>', 
            obj.processed_by.username if obj.processed_by else 'System'
        )
    action_buttons.short_description = 'Actions'
    
    def mark_as_processed(self, request, queryset):
        updated = queryset.update(
            is_processed=True,
            processed_by=request.user,
            processed_at=timezone.now()
        )
        self.message_user(request, f"{updated} requests marked as processed.")
    mark_as_processed.short_description = "Mark as processed"
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(
            is_processed=False,
            processed_by=None,
            processed_at=None
        )
        self.message_user(request, f"{updated} requests marked as pending.")
    mark_as_pending.short_description = "Mark as pending"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/create_user/',
                self.admin_site.admin_view(self.create_user),
                name='accounts_accessrequest_create_user',
            ),
            path(
                '<path:object_id>/reject_request/',
                self.admin_site.admin_view(self.reject_request),
                name='accounts_accessrequest_reject',
            ),
        ]
        return custom_urls + urls
    
    def create_user(self, request, object_id):
        try:
            access_request = AccessRequest.objects.get(id=object_id, is_processed=False)
            
            # Check if user with this email already exists
            if CustomUser.objects.filter(email=access_request.email).exists():
                messages.error(request, f"A user with email {access_request.email} already exists.")
                return redirect('admin:accounts_accessrequest_changelist')
            
            # Generate a valid username from the name
            username = self.generate_valid_username(access_request.name, access_request.email)
            
            # Generate a secure temporary password
            temp_password = secrets.token_urlsafe(12)
            
            # Create user
            user = CustomUser.objects.create_user(
                username=username,
                email=access_request.email,
                password=temp_password,
                first_name=access_request.name.split()[0] if access_request.name.split() else access_request.name,
                last_name=' '.join(access_request.name.split()[1:]) if len(access_request.name.split()) > 1 else '',
                user_type='student',
                is_approved=True,
                is_active=True
            )
            
            # Mark request as processed
            access_request.is_processed = True
            access_request.processed_by = request.user
            access_request.processed_at = timezone.now()
            access_request.save()
            
            # SUCCESS MESSAGE with credentials
            messages.success(
                request, 
                format_html(
                    "✅ <strong>User account created successfully!</strong><br>"
                    "📧 Email: {}<br>"
                    "👤 Username: <strong>{}</strong><br>"
                    "🔐 Temporary Password: <strong>{}</strong><br>"
                    "⚠️ <em>Please share these credentials with the user and ask them to change the password after first login.</em>",
                    access_request.email, username, temp_password
                )
            )
            
        except AccessRequest.DoesNotExist:
            messages.error(request, "Access request not found or already processed.")
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
        
        return redirect('admin:accounts_accessrequest_changelist')
    
    def reject_request(self, request, object_id):
        try:
            access_request = AccessRequest.objects.get(id=object_id, is_processed=False)
            
            # Mark request as processed (rejected)
            access_request.is_processed = True
            access_request.processed_by = request.user
            access_request.processed_at = timezone.now()
            access_request.save()
            
            messages.success(
                request, 
                f"❌ Access request from {access_request.name} ({access_request.email}) has been rejected."
            )
            
        except AccessRequest.DoesNotExist:
            messages.error(request, "Access request not found or already processed.")
        except Exception as e:
            messages.error(request, f"Error rejecting request: {str(e)}")
        
        return redirect('admin:accounts_accessrequest_changelist')
    
    def generate_valid_username(self, name, email):
        """
        Generate a valid Django username from name and email
        """
        # Use the name part before any spaces
        if ' ' in name:
            base_username = name.split(' ')[0].lower()
        else:
            base_username = name.lower()
        
        # Remove any non-allowed characters (only letters, numbers, and @/./+/-/_)
        base_username = re.sub(r'[^a-zA-Z0-9@\.\+\-_]', '', base_username)
        
        # If the name doesn't produce a valid username, use email prefix
        if not base_username:
            base_username = email.split('@')[0].lower()
            base_username = re.sub(r'[^a-zA-Z0-9@\.\+\-_]', '', base_username)
        
        # Ensure username is not empty
        if not base_username:
            base_username = "user"
        
        # Check if username already exists and find a unique one
        counter = 1
        original_username = base_username
        while CustomUser.objects.filter(username=base_username).exists():
            base_username = f"{original_username}{counter}"
            counter += 1
        
        return base_username
    
    def has_delete_permission(self, request, obj=None):
        # Only allow deletion for processed requests
        if obj and not obj.is_processed:
            return False
        return super().has_delete_permission(request, obj)
    
    def get_queryset(self, request):
        # Show newest requests first
        qs = super().get_queryset(request)
        return qs.order_by('-created_at')
