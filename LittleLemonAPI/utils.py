"""Utility functions for the Little Lemon API."""


def update_order_total(order):
    total = sum(item.price for item in order.items.all())
    order.total = total
    order.save(update_fields=['total'])


def is_authenticated(user):
    """Check if the user is authenticated.
    """
    return user.is_authenticated


def is_manager(user):
    """Check if the user is a manager.
    """
    if not is_authenticated(user):
        return False
    return user.groups.filter(name='Manager').exists()


def is_delivery_crew(user):
    """Check if the user is part of the delivery crew.
    """
    if not is_authenticated(user):
        return False
    return user.groups.filter(name='Delivery Crew').exists()


def is_customer(user):
    """Check if the user is a customer.
    """
    if not is_authenticated(user):
        return False    
    # A customer is not in the 'Manager' or 'Delivery Crew' groups
    if user.groups.filter(name__in=['Manager', 'Delivery Crew']).exists():
        return False
    return True

