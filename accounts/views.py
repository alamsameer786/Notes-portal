from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from accounts.models import CustomUser
from .forms import ForgotPasswordForm, ResetPasswordForm
from notes.models import Note
from .forms import AccessRequestForm, ProfileUpdateForm
from .models import AccessRequest
from django.contrib.auth import get_user_model
from .forms import ForgotPasswordForm, ResetPasswordForm
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model

# --- Login view ---
def login_view(request):
    if request.user.is_authenticated and request.method != 'POST':
        if request.user.is_superuser or request.user.user_type == 'admin':
            return redirect('admin_dashboard')
        else:
            return redirect('student_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next')

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'registration/login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, 'Your account has been deactivated. Please contact administrator.')
                return render(request, 'registration/login.html')
            login(request, user)
            if next_url:
                return HttpResponseRedirect(next_url)
            elif user.is_superuser or user.user_type == 'admin':
                return redirect('admin_dashboard')
            else:
                if user.is_approved:
                    return redirect('student_dashboard')
                else:
                    logout(request)
                    messages.error(request, 'Your account is not yet approved. Please wait for administrator approval.')
                    return render(request, 'registration/login.html')
        else:
            try:
                CustomUser.objects.get(username=username)
                messages.error(request, 'Invalid password. Please try again.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'Username does not exist. Please check your username or request access.')
            return render(request, 'registration/login.html')

    return render(request, 'registration/login.html')


# --- Request Access View ---
def request_access_view(request):
    if request.method == 'POST' and request.user.is_authenticated:
        logout(request)
    elif request.method == 'GET' and request.user.is_authenticated:
        if request.user.is_superuser or request.user.user_type == 'admin':
            return redirect('admin_dashboard')
        else:
            return redirect('student_dashboard')

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        reason = request.POST.get('reason')

        if not all([name, email, reason]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'accounts/request_access.html')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'accounts/request_access.html')

        if AccessRequest.objects.filter(email=email, is_processed=False).exists():
            messages.error(request, 'An access request with this email is already pending.')
            return render(request, 'accounts/request_access.html')

        try:
            AccessRequest.objects.create(name=name, email=email, reason=reason, is_processed=False)
            messages.success(request, 'Your access request has been submitted successfully! An administrator will review your request.')
            return redirect('login')
        except Exception as e:
            messages.error(request, 'An error occurred while processing your request. Please try again.')
            print(f"Error creating access request: {e}")

    return render(request, 'accounts/request_access.html')

User = get_user_model()
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'accounts/registration/forgot_password.html')

        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                messages.error(request, 'Your account is inactive. Please contact admin.')
                return render(request, 'accounts/registration/forgot_password.html')

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verify_url = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})

            return render(request, 'accounts/registration/email_verification_success.html', {'verify_url': verify_url})

        except User.DoesNotExist:
            messages.error(request, 'Your email is not registered. Please enter a correct email.')
            return render(request, 'accounts/registration/forgot_password.html')

    return render(request, 'accounts/registration/forgot_password.html')


def email_verification_success(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        messages.success(request, 'Email verified successfully! You may now reset your password.')
        verify_url = reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
        return render(request, 'accounts/registration/email_verification_success.html', {'verify_url': verify_url})
    else:
        messages.error(request, 'Invalid or expired verification link.')
        return redirect('forgot_password')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Invalid password reset link.')
        return redirect('forgot_password')

    if not default_token_generator.check_token(user, token):
        messages.error(request, 'Invalid or expired password reset token.')
        return redirect('forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Your password has been reset successfully. You can now log in.')
            return redirect('password_reset_done')
    else:
        form = ResetPasswordForm()
    return render(request, 'accounts/registration/password_reset_confirm.html', {'form': form})

def password_reset_done(request):
    return render(request, 'accounts/registration/password_reset_done.html')

# --- Logout View ---
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

# --- Student Dashboard ---
@login_required
def student_dashboard(request):
    user = request.user

    # Total number of notes uploaded by this user
    user_notes_count = Note.objects.filter(uploaded_by=user).count()

    # Sum of downloads over notes uploaded by this user (assuming downloads is integer field)
    user_downloads_count = Note.objects.filter(uploaded_by=user).aggregate(
        total_downloads=models.Sum('downloads')
    )['total_downloads'] or 0

    # Number of featured notes uploaded by this user
    featured_notes_count = Note.objects.filter(uploaded_by=user, is_featured=True).count()

    # Recent activities list
    recent_activities = []

    # Recent uploads by current user
    recent_uploads = Note.objects.filter(uploaded_by=user).order_by('-uploaded_at')[:3]
    for upload in recent_uploads:
        recent_activities.append({
            'type': 'upload',
            'message': f'You uploaded "{upload.title}"',
            'time': upload.uploaded_at,
            'icon': 'fa-upload',
            'color': 'success'
        })

    # Recent downloads of all notes (not filtered by user) with downloads > 0
    recent_downloaded_notes = Note.objects.filter(downloads__gt=0).order_by('-uploaded_at')[:5]
    for note in recent_downloaded_notes:
        recent_activities.append({
            'type': 'download',
            'message': f'Note "{note.title}" was downloaded',
            'time': note.uploaded_at,
            'icon': 'fa-download',
            'color': 'info'
        })

    # Sort all activities (uploads + downloads) by time descending
    recent_activities.sort(key=lambda x: x['time'], reverse=True)

    # Hall of fame featured notes
    hall_of_fame_notes = Note.objects.filter(is_featured=True).order_by('-uploaded_at')[:3]

    return render(request, 'accounts/student_dashboard.html', {
        'user_notes_count': user_notes_count,
        'user_downloads_count': user_downloads_count,
        'featured_notes_count': featured_notes_count,
        'recent_activities': recent_activities[:5],
        'hall_of_fame_notes': hall_of_fame_notes
    })

# --- Admin Dashboard ---
@login_required
@user_passes_test(lambda u: u.user_type == 'admin' or u.is_superuser)
def admin_dashboard(request):
    if not (request.user.is_superuser or request.user.user_type == 'admin'):
        messages.error(request, 'You do not have permission to access the admin dashboard.')
        return redirect('student_dashboard')

    pending_requests = AccessRequest.objects.filter(is_processed=False).order_by('-created_at')

    context = {
        'user': request.user,
        'total_users': CustomUser.objects.count(),
        'pending_approvals': CustomUser.objects.filter(is_approved=False, is_active=False).count(),
        'admin_users': CustomUser.objects.filter(user_type='admin').count(),
        'student_users': CustomUser.objects.filter(user_type='student').count(),
        'pending_requests': pending_requests,
        'total_pending_requests': pending_requests.count(),
    }
    return render(request, 'accounts/admin_dashboard.html', context)


# --- Process Access Request ---
@login_required
@user_passes_test(lambda u: u.user_type == 'admin' or u.is_superuser)
def process_access_request(request, request_id):
    if request.method == 'POST':
        try:
            access_request = AccessRequest.objects.get(id=request_id, is_processed=False)
            action = request.POST.get('action')

            if action == 'approve':
                username = access_request.email.split('@')[0]
                counter = 1
                original_username = username
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1

                import secrets
                temp_password = secrets.token_urlsafe(12)

                user = CustomUser.objects.create_user(
                    username=username,
                    email=access_request.email,
                    first_name=access_request.name.split()[0] if access_request.name.split() else access_request.name,
                    last_name=' '.join(access_request.name.split()[1:]) if len(access_request.name.split()) > 1 else '',
                    password=temp_password,
                    is_active=True,
                    is_approved=True,
                    user_type='student'
                )

                access_request.is_processed = True
                access_request.processed_by = request.user
                access_request.processed_at = timezone.now()
                access_request.save()

                print(f"User created: Username: {username}, Password: {temp_password}")
                messages.success(request, f'Access request approved! User {username} has been created.')

            elif action == 'reject':
                access_request.is_processed = True
                access_request.processed_by = request.user
                access_request.processed_at = timezone.now()
                access_request.save()
                messages.success(request, 'Access request has been rejected.')

        except AccessRequest.DoesNotExist:
            messages.error(request, 'Access request not found or already processed.')

    return redirect('admin_dashboard')


# --- Edit Profile ---
@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('edit_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/edit_profile.html', {'form': form})


# --- Change Password ---
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was changed successfully!')
            return redirect('edit_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


# --- Static Pages ---
def about_page(request):
    return render(request, 'pages/about.html')


def contact_page(request):
    if request.method == 'POST':
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('contact')
    return render(request, 'pages/contact.html')


def feedback_page(request):
    if request.method == 'POST':
        messages.success(request, 'Thank you for your feedback! We appreciate your input.')
        return redirect('feedback')
    return render(request, 'pages/feedback.html')


@login_required
def settings_page(request):
    if request.method == 'POST':
        theme = request.POST.get('theme', 'light')
        request.session['theme'] = theme
        messages.success(request, 'Settings saved successfully!')
        return redirect('settings')

    current_theme = request.session.get('theme', 'light')

    return render(request, 'accounts/settings.html', {'current_theme': current_theme})
