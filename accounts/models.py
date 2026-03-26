from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """
    Extends the built-in Django User model to include common details 
    for all users (both customers and providers).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_provider = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class ServiceProvider(models.Model):
    """
    Stores specific professional details for users who register as service providers.
    """
    SERVICE_CATEGORIES = [
        ('plumber', 'Plumber'),
        ('electrician', 'Electrician'),
        ('cleaner', 'Cleaner'),
        ('tutor', 'Tutor'),
        ('carpenter', 'Carpenter'),
        ('painter', 'Painter'),
        ('mechanic', 'Mechanic'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')
    service_category = models.CharField(max_length=50, choices=SERVICE_CATEGORIES)
    location = models.CharField(max_length=100)
    
    # NEW: Geolocation for Provider's base of operations
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    bio = models.TextField()
    experience_years = models.PositiveIntegerField()
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    profile_picture = models.ImageField(upload_to='provider_pics/', blank=True, null=True)
    is_verified = models.BooleanField(default=True)
    recommendation_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.user.username} - {self.get_service_category_display()}"