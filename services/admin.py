from django.contrib import admin
from .models import Booking, Review, EmergencyJob

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

# NEW: Register the EmergencyJob with a nice display layout
@admin.register(EmergencyJob)
class EmergencyJobAdmin(admin.ModelAdmin):
    list_display = ('customer', 'service_category', 'status', 'created_at')
    list_filter = ('status', 'service_category')
    readonly_fields = ('created_at',)