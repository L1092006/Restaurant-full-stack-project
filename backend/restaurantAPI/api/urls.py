from django.urls import path
from . import views

app_name = 'myAPI'

urlpatterns = [
    path('auth/login/', views.LoginView.as_view(), name="login"),
    path('auth/refresh/', views.RefreshView.as_view(), name="refresh"),
    path('auth/logout/', views.LogoutView.as_view(), name="logout"),
]