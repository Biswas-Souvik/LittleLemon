"""Utility functions for the Little Lemon API."""


def update_order_total(order):
    total = sum(item.price for item in order.items.all())
    order.total = total
    order.save(update_fields=['total'])

