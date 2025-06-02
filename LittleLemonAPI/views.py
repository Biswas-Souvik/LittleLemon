from django.shortcuts import render
from django.contrib.auth.models import User, Group

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MenuItem, Cart, Order, OrderItem
from .serializers import UserSerializer, CurrentUserSerializer, MenuItemSerializer,\
    CartSerializer, OrderSerializer
from .permissions import IsManager, IsCustomer
from .utils import is_customer, is_manager, is_delivery_crew, update_order_total

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
            return User.objects.get(id=self.kwargs['pk'])
        except User.DoesNotExist:
            return None

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user is None:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        manager_group = Group.objects.get(name="Manager")
        manager_group.user_set.remove(user)
        return Response({"detail": f"User '{user.username}' removed from Manager group."}, status=status.HTTP_200_OK)


class DeliveryCrewListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = UserSerializer

    def get_queryset(self):
        try:
            delivery_crew_group = Group.objects.get(name="Delivery Crew")
            return delivery_crew_group.user_set.all()
        except Group.DoesNotExist:
            return User.objects.none()

    def create(self, request, *args, **kwargs):
        username = request.data.get("username")
        if not username:
            return Response({"detail": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(username=username)
            delivery_crew_group, _ = Group.objects.get_or_create(name="Delivery Crew")
            delivery_crew_group.user_set.add(user)
            return Response({"detail": f"User '{username}' added to Delivery Crew group."}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)


class DeliveryCrewRemoveView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = UserSerializer

    def get_object(self):
        try:
            return User.objects.get(pk=self.kwargs['pk'])
        except User.DoesNotExist:
            return None

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user is None:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        delivery_crew_group = Group.objects.get(name="Delivery Crew")
        delivery_crew_group.user_set.remove(user)
        return Response({"detail": f"User '{user.username}' removed from Delivery Crew group."}, status=status.HTTP_200_OK)


class CartListCreateRemoveView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        menu_item_id = request.data.get('menu_item_id')
        quantity = request.data.get('quantity')

        try:
            menu_item = MenuItem.objects.get(id=menu_item_id)
        except MenuItem.DoesNotExist:
            return Response({'error': 'MenuItem ID not found'}, status=status.HTTP_404_NOT_FOUND)

        unit_price = menu_item.price
        price = unit_price * int(quantity)

        cart_item, _ = Cart.objects.update_or_create(
            user=request.user,
            menu_item=menu_item,
            defaults={'quantity': quantity, 'unit_price': unit_price, 'price': price}
        )

        serializer = self.get_serializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_200_OK)
    

class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if is_manager(user):
            return Order.objects.all()
        if is_delivery_crew(user):
            return Order.objects.filter(delivery_crew=user)
        return Order.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        user = request.user
        if not is_customer(user):
            return Response({"detail": "You do not have permission to create an order."}, status=status.HTTP_403_FORBIDDEN)

        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user=user)

        order_items = []
        for item in cart_items:
            order_item = OrderItem(
                order=order,
                menu_item=item.menu_item,
                quantity=item.quantity,
                unit_price=item.unit_price,
                price=item.price
            )
            order_items.append(order_item)

        OrderItem.objects.bulk_create(order_items)
        update_order_total(order)

        cart_items.delete()     # clear the cart after order creation

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsCustomer]
    queryset = Order.objects.all()  # Required for RetrieveAPIView

    def get(self, request, *args, **kwargs):
        order = self.get_object()
        if request.user != order.user:
            return Response({"detail": "You do not have permission to see this order."}, status=status.HTTP_403_FORBIDDEN)
        return super().get(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        order = self.get_object()
        if request.user != order.user:
            return Response({"detail": "You do not have permission to update this order."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        if request.user != order.user:
            return Response({"detail": "You do not have permission to update this order."}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)
    
