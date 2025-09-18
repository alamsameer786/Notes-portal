from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator

from .forms import NoteUploadForm, NoteFilterForm
from .models import Note, Subject, Semester

@login_required
def hall_of_fame(request):
    featured_notes = Note.objects.filter(is_featured=True).order_by('-uploaded_at')
    return render(request, 'notes/hall_of_fame.html', {'featured_notes': featured_notes})

@login_required
def upload_notes(request):
    if request.method == 'POST':
        form = NoteUploadForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.uploaded_by = request.user
            note.save()
            messages.success(request, 'Your notes have been uploaded successfully!')
            return redirect('upload_notes')
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = NoteUploadForm()
    
    # Get available subjects and semesters for the template
    subjects = Subject.objects.filter(is_active=True).order_by('semester', 'name')
    semesters = Semester.objects.all().order_by('number')
    
    return render(request, 'notes/upload_notes.html', {
        'form': form,
        'subjects': subjects,
        'semesters': semesters
    })

@login_required
def download_notes(request):
    notes = Note.objects.all().order_by('-uploaded_at')  # Show all notes
    # Initialize filter form
    filter_form = NoteFilterForm(request.GET)
    
    # Start with all notes
    notes = Note.objects.select_related('subject', 'semester', 'uploaded_by').all()
    Note.objects.filter(id=note_id).update(downloads=models.F('downloads') + 1)
    # Apply filters
    if filter_form.is_valid():
        subject = filter_form.cleaned_data.get('subject')
        semester = filter_form.cleaned_data.get('semester')
        category = filter_form.cleaned_data.get('category')
        search_query = filter_form.cleaned_data.get('q')
        
        if subject:
            notes = notes.filter(subject=subject)
        if semester:
            notes = notes.filter(semester=semester)
        if category:
            notes = notes.filter(category=category)
        if search_query:
            notes = notes.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(subject__name__icontains=search_query)
            )
    
    # Pagination
    paginator = Paginator(notes, 10)  # Show 10 notes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all subjects and semesters for filter dropdowns
    subjects = Subject.objects.filter(is_active=True).order_by('semester', 'name')
    semesters = Semester.objects.all().order_by('number')
    
    context = {
        'notes': page_obj,
        'filter_form': filter_form,
        'subjects': subjects,
        'semesters': semesters,
        'selected_subject': request.GET.get('subject'),
        'selected_semester': request.GET.get('semester'),
        'selected_category': request.GET.get('category'),
        'search_query': request.GET.get('q', ''),
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    return render(request, 'notes/download_notes.html', context)

@login_required
def preview_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    
    # Check if it's a PDF file
    if note.file.name.lower().endswith('.pdf'):
        try:
            response = HttpResponse(note.file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{note.title}.pdf"'
            return response
        except:
            messages.error(request, 'Unable to preview this file.')
            return redirect('download_notes')
    else:
        messages.info(request, 'Preview is only available for PDF files. Downloading file instead.')
        return download_note_file(request, note_id)

@login_required
def download_note_file(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    
    # Increment download count
    note.downloads += 1
    note.save()
    
    try:
        response = HttpResponse(note.file.read(), content_type='application/force-download')
        response['Content-Disposition'] = f'attachment; filename="{note.title}_{note.file.name}"'
        return response
    except:
        messages.error(request, 'File not found or corrupted.')
        return redirect('download_notes')
