from django.urls import path, include

from . import views


urlpatterns = [
    path('auth', include('rest_framework.urls')),
    path('users', views.CreateUserView.as_view(), name='create_user'),
    path('users/user/me/', views.CurrentUserView.as_view(), name='current-user'),

    #  Menu-items endpoints
    path('menu-items', views.MenuItemListCreateView.as_view(), name='menu-items'),
    path('menu-items/<int:pk>', views.MenuItemDetailView.as_view(), name='menu-item-detail'),
]