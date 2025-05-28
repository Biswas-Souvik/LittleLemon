from django.urls import path, include

from . import views


urlpatterns = [
    path('auth', include('rest_framework.urls')),
    path('users', views.UserCreate.as_view(), name='create_user'),
]