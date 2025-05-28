from django.urls import path, include

from . import views


urlpatterns = [
    path('auth', include('rest_framework.urls')),
    path('users', views.CreateUserView.as_view(), name='create_user'),
    path('users/user/me/', views.CurrentUserView.as_view(), name='current_user'),

    #  Menu-items endpoints
    path('menu-items', views.MenuItemListCreateView.as_view(), name='menu_items'),
]