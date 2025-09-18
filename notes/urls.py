from django.urls import path
from . import views

urlpatterns = [
    path('hall-of-fame/', views.hall_of_fame, name='hall_of_fame'),
    path('upload/', views.upload_notes, name='upload_notes'),
    path('download/', views.download_notes, name='download_notes'),
    path('download/<int:note_id>/', views.download_note_file, name='download_note_file'),
    path('preview/<int:note_id>/', views.preview_note, name='preview_note'),  # Add this
]