# users/permissions.py

from rest_framework.permissions import BasePermission

class IsManager(BasePermission):
    """
    Allows access only to users in the 'manager' group.
    """

    def has_permission(self, request, view):
        return request.user.groups.filter(name='Manager').exists()


class IsCustomer(BasePermission):
    """
    Allows access only to users who are not in the 'Manager' or 'Delivery Crew' groups.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.groups.filter(name__in=['Manager', 'Delivery Crew']).exists():
            return False
        return True