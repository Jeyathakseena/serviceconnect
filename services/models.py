from django.db import models
from django.contrib.auth.models import User
# Importing ServiceProvider from the accounts app models
from accounts.models import ServiceProvider

# 1. Booking model: Stores details about a service appointment
class Booking(models.Model):
    # Choices for the booking status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # The user who is making the booking (Customer)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    
    # The professional being booked (from the accounts app)
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='bookings')
    
    # The date the service will take place
    service_date = models.DateField()
    
    # The specific time for the service
    service_time = models.TimeField()
    
    # Detailed notes on what the user needs help with
    description = models.TextField()
    
    # Current state of the booking, defaults to 'pending'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Automatically records when this entry was created
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking: {self.user.username} with {self.provider.user.username}"


# 2. Review model: Stores feedback left by users after a service
class Review(models.Project):
    # Rating options from 1 to 5 stars
    RATING_CHOICES = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ]

    # Links this review to a specific booking (one review per booking)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    
    # The user writing the review
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_written')
    
    # The service provider receiving the review
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='reviews_received')
    
    # The numerical score given by the user
    rating = models.IntegerField(choices=RATING_CHOICES)
    
    # The written feedback text
    comment = models.TextField()
    
    # Automatically records when the review was posted
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.provider.user.username} - Rating: {self.rating}"