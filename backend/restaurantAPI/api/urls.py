from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

# Initialize router
router = DefaultRouter()
router.register('items', views.MenuItemView, basename='menuitem')
router.register('categories', views.CategoryView, basename='category')
router.register('carts', views.CartView, basename='cart')

urlpatterns = [
    path('auth/login/', views.LoginView.as_view(), name="login"),
    path('auth/refresh/', views.RefreshView.as_view(), name="refresh"),
    path('auth/logout/', views.LogoutView.as_view(), name="logout"),
    path('auth/signup/', views.SignUpView.as_view(), name="signup"),
    path('users/<str:pk>/', views.SingleCustomerView.as_view(), name="single_customer"),
    path('', include(router.urls)),
]
