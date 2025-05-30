from django.shortcuts import render
from django.contrib.auth.models import User, Group

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MenuItem, Cart, Order
from .serializers import UserSerializer, CurrentUserSerializer, MenuItemSerializer,\
    CartSerializer, OrderSerializer, OrderItemSerializer
from .permissions import IsManager, IsCustomer


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


class CartListCreateRemoveView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data)

    def post(self, request):
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

        serializer = CartSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_200_OK)
    

class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user        
        
        if user.groups.filter(name='Manager').exists():
            orders = Order.objects.all()
        elif user.groups.filter(name='Delivery Crew').exists():
            orders = Order.objects.filter(delivery_crew=user)
        else:
            orders = Order.objects.filter(user=user)

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)