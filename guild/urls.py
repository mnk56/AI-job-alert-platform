from django.urls import path
from . import views

app_name = 'guild'

urlpatterns = [
    path('', views.index, name='index'),
    path('company/new/', views.company_create, name='company_create'),
    path('company/<int:pk>/', views.company_detail, name='company_detail'), 
    path('company/<int:company_pk>/start/', views.session_start, name='session_start'),
    path('session/<int:pk>/', views.session_detail, name='session_detail'),
    path('session/<int:session_pk>/post/', views.chatlog_post, name='chatlog_post'),
    path('session/<int:pk>/finish/', views.session_finish, name='session_finish'),
    path('stats/', views.stats, name='stats'),
]