from django.contrib import admin
from .models import UserProfile, ServiceProvider

# Register the UserProfile model with default admin settings
admin.site.register(UserProfile)

# Register the ServiceProvider model with customized list view and search
@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    # Columns to display in the admin list view
    list_display = ('user', 'service_category', 'location', 'is_verified', 'recommendation_score')
    
    # Fields that can be searched in the admin panel
    # We use 'user__username' to span the relationship and search the Django User's username
    search_fields = ('user__username', 'location')