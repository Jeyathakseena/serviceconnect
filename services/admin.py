from django.contrib import admin
from .models import Booking, Review

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # Columns to show in the admin list view
    list_display = ('user', 'provider', 'service_date', 'status')
    
    # Adds a filter sidebar to sort bookings by their status
    list_filter = ('status',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    # Columns to show in the admin list view
    list_display = ('reviewer', 'provider', 'rating')