from django.contrib import admin
# Importing the models you just created in Step 2
from .models import Booking, Review

# 1. Registering the Booking model to the admin panel
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # Columns that will appear in the admin list view
    list_display = ('user', 'provider', 'service_date', 'status')
    
    # Adds a sidebar to filter bookings by their current status
    list_filter = ('status',)

# 2. Registering the Review model to the admin panel
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    # Columns that will appear in the admin list view
    list_display = ('reviewer', 'provider', 'rating')