from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Category, MenuItem, Cart, OrderItem, Order


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
    
    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']

        user = User.objects.create_user(
            username=username, email=email, password=password
        )

        return user


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id']


class CartSerializer(serializers.ModelSerializer):
    item = serializers.ReadOnlyField(source='menu_item.title')

    class Meta:
        model = Cart
        fields = ['item', 'quantity', 'unit_price', 'price']


class OrderItemSerializer(serializers.ModelSerializer):
    item = serializers.ReadOnlyField(source='menu_item.title')
    class Meta:
        model = OrderItem
        fields = ['item', 'unit_price', 'quantity', 'price']
        read_only_fields = ['unit_price', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.ReadOnlyField(source='user.username')
    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date', 'items']
        read_only_fields = ['total']

