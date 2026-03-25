from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Custom registration and profile views
    path('register/', views.register_user, name='register'),
    path('register/provider/', views.register_provider, name='register_provider'),
    path('profile/', views.profile, name='profile'),
    
    # Django's built-in authentication views
    # We specify the template name so Django knows where to look for our custom login page
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    # The next_page argument tells Django where to redirect after logging out
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]