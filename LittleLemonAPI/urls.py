from django.urls import path, include

from . import views


urlpatterns = [
    path('auth', include('rest_framework.urls')),
    path('users', views.CreateUserView.as_view(), name='create-user'),
    path('users/user/me/', views.CurrentUserView.as_view(), name='current-user'),

    #  Menu-items endpoints
    path('menu-items', views.MenuItemListCreateView.as_view(), name='menu-items'),
    path('menu-items/<int:pk>', views.MenuItemDetailView.as_view(), name='menu-item-detail'),

    # User group management endpoints
    path('groups/manager/users', views.ManagerListCreateView.as_view(), name='manager-users'),
    path('groups/manager/users/<str:username>', views.ManagerRemoveView.as_view(), name='remove-manager'),    
]