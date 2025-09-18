from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Semester(models.Model):
    number = models.IntegerField(unique=True)
    name = models.CharField(max_length=50)
    
    class Meta:
        ordering = ['number']
    
    def __str__(self):
        return f"Semester {self.number}"

class Subject(models.Model):
    SEMESTER_CHOICES = [
        (1, 'Semester 1'),
        (2, 'Semester 2'),
        (3, 'Semester 3'),
        (4, 'Semester 4'),
        (5, 'Semester 5'),
        (6, 'Semester 6'),
        (7, 'Semester 7'),
        (8, 'Semester 8'),
    ]
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    semester = models.IntegerField(choices=SEMESTER_CHOICES)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['semester', 'name']
    
    def __str__(self):
        return f"{self.name} (SEM {self.semester})"

class Note(models.Model):
    CATEGORY_CHOICES = [
        ('notes', 'Notes'),
        ('assignments', 'Assignments'),
        ('previous_papers', 'Previous Year Papers'),
        ('lab_manuals', 'Lab Manuals'),
        ('presentations', 'Presentations'),
        ('study_materials', 'Study Materials'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='notes')
    file = models.FileField(upload_to='notes/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    downloads = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return f"{self.title} - {self.subject.name}"
    
    def get_file_size(self):
        """Return file size in MB"""
        try:
            return round(self.file.size / (1024 * 1024), 2)
        except:
            return 0
