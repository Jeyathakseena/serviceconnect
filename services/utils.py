from django.db.models import Avg
from .models import Review, Booking
from accounts.models import ServiceProvider

"""
SERVICE_CONNECT RECOMMENDATION ENGINE (v1.0)
Type: Rule-Based Heuristic Scoring System

This utility calculates a 'Trust & Quality' score for service providers 
using a weighted multi-factor formula. This ensures that new providers 
with one 5-star review don't instantly outrank veterans with hundreds 
of 4.8-star reviews.
"""

def calculate_recommendation_score(provider):
    """
    Calculates a weighted score from 0.0 to 5.0 for a specific provider.
    
    Weights Breakdown:
    - 50% Quality (Average Rating)
    - 30% Social Proof (Review Count)
    - 20% Reliability (Completion Rate)
    """
    
    # FACTOR 1: QUALITY (50% Weight)
    # Why: The most direct indicator of customer satisfaction.
    reviews = Review.objects.filter(provider=provider)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
    
    # FACTOR 2: SOCIAL PROOF (30% Weight)
    # Why: A provider with 50 reviews is more 'proven' than one with 2.
    # Normalization: We cap the 'full credit' at 10 reviews.
    review_count = reviews.count()
    normalized_reviews = min(review_count / 10, 1) * 5
    
    # FACTOR 3: RELIABILITY (20% Weight)
    # Why: Rewards providers who actually show up and finish the job.
    # Normalization: We cap 'full credit' at 20 completed bookings.
    completed_bookings = Booking.objects.filter(provider=provider, status='completed').count()
    normalized_bookings = min(completed_bookings / 20, 1) * 5
    
    # THE FINAL HEURISTIC FORMULA
    # We multiply each normalized factor (all on a 0-5 scale) by its weight.
    score = (avg_rating * 0.5) + (normalized_reviews * 0.3) + (normalized_bookings * 0.2)
    
    return round(float(score), 2)

def update_all_scores():
    """
    Maintenance function to refresh the recommendation scores for the entire
    marketplace. This can be called via a Cron job or a management command.
    """
    providers = ServiceProvider.objects.all()
    updated_count = 0
    
    for provider in providers:
        new_score = calculate_recommendation_score(provider)
        provider.recommendation_score = new_score
        provider.save()
        updated_count += 1
        
    return updated_count