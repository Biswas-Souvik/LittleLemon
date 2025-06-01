"""Permissions for Little Lemon API."""

from rest_framework.permissions import BasePermission

from .utils import is_customer, is_manager


class IsManager(BasePermission):
    """
    Allows access only to users in the 'manager' group.
    """

    def has_permission(self, request, view):
        return is_manager(request.user)


class IsCustomer(BasePermission):
    """
    Allows access only to users who are not in the 'Manager' or 'Delivery Crew' groups.
    """

    def has_permission(self, request, view):
        return is_customer(request.user)
    
