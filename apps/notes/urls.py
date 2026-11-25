from django.urls import path
from . import views

urlpatterns = [
    path('', views.note_list_view, name='note_list'),
    path('create/', views.note_create_view, name='note_create'),
    path('new/', views.note_create_view, name='note_new'),
    path('<int:note_id>/edit/', views.note_edit_view, name='note_edit'),
    path('<int:note_id>/delete/', views.note_delete_view, name='note_delete'),
    path('<int:note_id>/toggle-pin/', views.note_toggle_pin_view, name='note_toggle_pin'),
    path('<int:note_id>/pin/', views.note_toggle_pin_view, name='note_pin'),
]


