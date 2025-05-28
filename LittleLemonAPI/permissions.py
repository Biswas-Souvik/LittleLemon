# users/permissions.py

from rest_framework.permissions import BasePermission

class IsManager(BasePermission):
    """
    Allows access only to users in the 'manager' group.
    """

    def has_permission(self, request, view):
        return request.user.groups.filter(name='Manager').exists()
