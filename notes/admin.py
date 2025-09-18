from django.contrib import admin
from .models import Subject, Semester, Note

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('number',)
    list_filter = ('number',)

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'semester', 'uploaded_by', 'uploaded_at', 'is_featured')
    list_filter = ('subject', 'semester', 'is_featured', 'uploaded_at')
    search_fields = ('title', 'description')
    readonly_fields = ('downloads', 'uploaded_at')
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
    make_featured.short_description = "Mark selected notes as featured"
    
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
    remove_featured.short_description = "Remove featured status from selected notes"
    
    actions = [make_featured, remove_featured]