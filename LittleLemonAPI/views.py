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
    

class OrderDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.all()

    def get(self, request, *args, **kwargs):
        order = self.get_object()
        user = request.user
        
        # Customers can only see their own orders
        if is_customer(user) and order.user != user:
            return Response({"detail": "You do not have permission to see this order."}, status=status.HTTP_403_FORBIDDEN)
        # Managers and others can see all orders (adjust as needed)
        return super().get(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        user = request.user
        data = request.data

        # Customer can only update their own orders (except delivery crew and status)
        if is_customer(user):
            if order.user != user:
                return Response({"detail": "You do not have permission to update this order."}, status=status.HTTP_403_FORBIDDEN)
            # Prevent customers from updating delivery_crew or status
            if 'delivery_crew' in data or 'status' in data:
                return Response({"detail": "Customers cannot update delivery crew or status."}, status=status.HTTP_403_FORBIDDEN)

        # Manager can update delivery_crew and status with restrictions
        elif is_manager(user):
            # Validate delivery_crew user if provided
            delivery_crew_id = data.get('delivery_crew')
            status_val = data.get('status')

            if delivery_crew_id is not None:
                try:
                    delivery_crew_user = User.objects.get(id=delivery_crew_id)
                    if not delivery_crew_user.groups.filter(name='Delivery Crew').exists():
                        return Response({"detail": "Assigned user is not a delivery crew."}, status=status.HTTP_400_BAD_REQUEST)
                except User.DoesNotExist:
                    return Response({"detail": "Delivery crew user not found."}, status=status.HTTP_404_NOT_FOUND)
                # Set the delivery crew
                order.delivery_crew = delivery_crew_user

            if status_val is not None:
                if int(status_val) not in [0, 1]:
                    return Response({"detail": "Status must be 0 (out for delivery) or 1 (delivered)."}, status=status.HTTP_400_BAD_REQUEST)
                order.status = int(status_val)

            order.save()

            # After manager update, refresh data for serializer
            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif is_delivery_crew(user):
            if order.delivery_crew != user:
                return Response({"detail": "You are not assigned to this order."}, status=status.HTTP_403_FORBIDDEN)

            if 'status' in data:
                status_val = int(data['status'])
                if status_val not in [0, 1]:
                    return Response({"detail": "Status must be 0 or 1."}, status=status.HTTP_400_BAD_REQUEST)
                order.status = status_val
                order.save()
                serializer = self.get_serializer(order)
                return Response(serializer.data)
            else:
                return Response({"detail": "Only 'status' field can be updated."}, status=status.HTTP_400_BAD_REQUEST)


        # For other roles, deny update (or extend your rules)
        if not is_customer(user):
            return Response({"detail": "You do not have permission to update this order."}, status=status.HTTP_403_FORBIDDEN)

        # If customer and allowed to update (not delivery_crew or status), do normal update
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        order = self.get_object()
        user = request.user

        if not is_manager(user):
            return Response({"detail": "Only managers can delete orders."}, status=status.HTTP_403_FORBIDDEN)

        order.delete()
        return Response(status=status.HTTP_200_OK)