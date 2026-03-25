from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """
    Extends the built-in Django User model to include common details 
    for all users (both customers and providers).
    """
    # Links this profile to exactly one Django User instance
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Optional phone number for contact (blank=True, null=True makes it optional)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Optional physical address or general location text
    address = models.TextField(blank=True, null=True)
    
    # Flag to easily distinguish regular customers from service providers
    is_provider = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class ServiceProvider(models.Model):
    """
    Stores specific professional details for users who register as service providers.
    """
    # Pre-defined choices for the service_category field
    SERVICE_CATEGORIES = [
        ('plumber', 'Plumber'),
        ('electrician', 'Electrician'),
        ('cleaner', 'Cleaner'),
        ('tutor', 'Tutor'),
        ('carpenter', 'Carpenter'),
        ('painter', 'Painter'),
        ('mechanic', 'Mechanic'),
    ]

    # Links this provider profile to exactly one Django User instance
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')
    
    # Dropdown selection for the specific type of service offered
    service_category = models.CharField(max_length=50, choices=SERVICE_CATEGORIES)
    
    # The city or general area where the provider operates
    location = models.CharField(max_length=100)
    
    # A detailed description of the provider's skills, background, and offerings
    bio = models.TextField()
    
    # Number of years the provider has been working in their field
    experience_years = models.PositiveIntegerField()
    
    # Cost per hour for the provider's services (up to 999,999.99)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Optional image upload for the provider's profile picture
    # Files will be uploaded to MEDIA_ROOT/provider_pics/
    profile_picture = models.ImageField(upload_to='provider_pics/', blank=True, null=True)
    
    # Flag indicating if the system/admin has verified this provider's credentials
    is_verified = models.BooleanField(default=True)
    
    # An aggregated score based on customer reviews (e.g., 4.95)
    recommendation_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)

    def __str__(self):
        # Uses Django's get_FOO_display() to show the readable choice name (e.g., "Plumber" instead of "plumber")
        return f"{self.user.username} - {self.get_service_category_display()}"