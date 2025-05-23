from django.shortcuts import render
from .models import MenuItem, Category, Rating
from .serializers import MenuItemSerializer, CategorySerializer, RatingSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated


# Create your views here.
class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price', 'inventory']
    filterset_fields = ['price', 'inventory']
    search_fields = ['category']


class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer


class RatingsView(generics.ListCreateAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    
    def get_permissions(self):
        if(self.request.method=='GET'):
            return []
        return [IsAuthenticated()]