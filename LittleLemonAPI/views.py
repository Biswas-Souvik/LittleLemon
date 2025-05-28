from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics

from .serializers import UserSerializer

# Create your views here.
class UserCreate(generics.CreateAPIView):
    model = User
    serializer_class = UserSerializer
    permission_classes = []

