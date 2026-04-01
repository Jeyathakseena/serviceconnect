from django.db import models
from django.contrib.auth.models import User
from accounts.models import ServiceProvider

class Booking(models.Model):
    """
    Represents a service request made by a user to a specific service provider.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # The user who made the booking
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    
    # The service provider being booked
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='provider_bookings')
    
    # The date the service is requested for
    service_date = models.DateField()
    
    # The specific time the service is requested for
    service_time = models.TimeField()

    # NEW: Location Fields
    address = models.TextField(help_text="Exact address for the service")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Details about what service is needed
    description = models.TextField()
    
    # The current status of the booking request (defaults to pending)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Automatically set to the exact date and time the booking was created
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking by {self.user.username} for {self.provider.user.username} on {self.service_date}"


class Review(models.Model):
    """
    Represents a review left by a user for a service provider after a booking.
    """
    RATING_CHOICES = [
        (1, '1 - Very Poor'),
        (2, '2 - Poor'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]

    # The specific booking this review is linked to (ensures only one review per booking)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    
    # The user who wrote the review
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    
    # The service provider being reviewed
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='received_reviews')
    
    # The rating given by the user, from 1 to 5
    rating = models.IntegerField(choices=RATING_CHOICES)
    
    # The written feedback from the user
    comment = models.TextField()
    
    # Automatically set to the exact date and time the review was submitted
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.provider.user.username} - {self.rating} Stars"

class EmergencyJob(models.Model):
    """
    Represents a real-time, high-priority SOS request broadcasted to nearby providers.
    Expires automatically if not accepted within a short timeframe.
    """
    STATUS_CHOICES = [
        ('searching', 'Searching for Providers'),
        ('accepted', 'Accepted by Provider'),
        ('expired', 'Expired (No Response)'),
    ]

    # Who is experiencing the emergency?
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergencies')
    
    # What kind of help do they need? (e.g., 'plumber', 'electrician')
    service_category = models.CharField(max_length=100)
    
    # Exact location of the emergency for the radius radar
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    # The current state of the SOS beacon
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='searching')
    
    # The specific provider who clicked "Accept" first. (Blank until someone claims it)
    accepted_by = models.ForeignKey(
        ServiceProvider, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='claimed_emergencies'
    )
    
    # The timestamp. This is critical for our 10-minute expiration math!
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SOS: {self.service_category} needed by {self.customer.username} at {self.created_at.strftime('%H:%M')}"