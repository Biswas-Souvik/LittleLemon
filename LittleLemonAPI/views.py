from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import MenuItem
from .serializers import UserSerializer, CurrentUserSerializer, MenuItemSerializer
from .permissions import IsManager
from django.contrib.auth.models import Group
from rest_framework.response import Response
from rest_framework import status

# Create your views here.
class CreateUserView(generics.CreateAPIView):
    model = User
    serializer_class = UserSerializer
    permission_classes = []


class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = CurrentUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class MenuItemListCreateView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        permissions = [IsAuthenticated()]

        if self.request.method == 'POST':
            permissions.append(IsManager())

        return permissions
    

class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        permissions = [IsAuthenticated()]

        if self.request.method != 'GET':
            permissions.append(IsManager())

        return permissions
    

class ManagerListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = UserSerializer

    def get_queryset(self):
        try:
            manager_group = Group.objects.get(name="Manager")
            return manager_group.user_set.all()
        except Group.DoesNotExist:
            return User.objects.none()

    def create(self, request, *args, **kwargs):
        username = request.data.get("username")
        if not username:
            return Response({"detail": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(username=username)
            manager_group, _ = Group.objects.get_or_create(name="Manager")
            manager_group.user_set.add(user)
            return Response({"detail": f"User '{username}' added to Manager group."}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)


class ManagerRemoveView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = UserSerializer

    def get_object(self):
        try:
            return User.objects.get(username=self.kwargs['username'])
        except User.DoesNotExist:
            return None

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user is None:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        manager_group = Group.objects.get(name="Manager")
        manager_group.user_set.remove(user)
        return Response({"detail": f"User '{user.username}' removed from Manager group."}, status=status.HTTP_200_OK)

