from django.urls import path, include

from . import views


urlpatterns = [
    path('users', views.UserCreate.as_view(), name='create_user'),
]