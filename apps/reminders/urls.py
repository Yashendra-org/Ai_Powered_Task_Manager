from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list_view, name='notification_list'),
    path('inbox/', views.notification_list_view, name='notification_inbox'),
    path('<int:notification_id>/read/', views.notification_mark_read_view, name='notification_mark_read'),
    path('read-all/', views.notification_mark_all_read_view, name='notification_mark_all_read'),
    path('mark-all-read/', views.notification_mark_all_read_view, name='notification_mark_all_read_alias'),
]


