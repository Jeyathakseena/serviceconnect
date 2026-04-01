from django.urls import path
from . import views

urlpatterns = [
    # Core browsing
    path('', views.homepage, name='home'),
    path('search/', views.search_providers, name='search'),
    path('provider/<int:provider_id>/', views.provider_profile, name='provider_profile'),
    
    # Booking flow
    path('book/<int:provider_id>/', views.create_booking, name='create_booking'),
    path('bookings/', views.my_bookings, name='my_bookings'),
    path('booking/update/<int:booking_id>/<str:new_status>/', views.update_booking_status, name='update_booking'),
    
    # Provider management and reviews
    path('dashboard/', views.provider_dashboard, name='provider_dashboard'),
    path('review/<int:booking_id>/', views.submit_review, name='submit_review'),

    path('sos/trigger/', views.trigger_emergency, name='trigger_emergency'),
    path('sos/radar/<int:emergency_id>/', views.emergency_radar, name='emergency_radar'),

    path('api/check-emergencies/', views.check_emergencies, name='check_emergencies'),
    path('sos/accept/<int:emergency_id>/', views.accept_emergency, name='accept_emergency'),
]