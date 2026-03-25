from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from accounts.models import ServiceProvider
from .models import Review, Booking
from .utils import update_all_scores  # Importing our scoring engine

# ==========================================
# DISCOVERY & SEARCH VIEWS
# ==========================================

def homepage(request):
    """Displays top-rated providers and service categories."""
    top_providers = ServiceProvider.objects.all().order_by('-recommendation_score')[:6]
    categories = ServiceProvider.SERVICE_CATEGORIES
    context = {
        'top_providers': top_providers,
        'SERVICE_CATEGORIES': categories,
    }
    return render(request, 'services/home.html', context)

def search_providers(request):
    """Filters providers by category and location."""
    category_query = request.GET.get('category', '')
    location_query = request.GET.get('location', '')
    providers = ServiceProvider.objects.all()

    if category_query:
        providers = providers.filter(service_category=category_query)
    if location_query:
        providers = providers.filter(location__icontains=location_query)

    providers = providers.order_by('-recommendation_score')

    context = {
        'providers': providers,
        'category': category_query,
        'location': location_query,
        'SERVICE_CATEGORIES': ServiceProvider.SERVICE_CATEGORIES,
    }
    return render(request, 'services/search_results.html', context)

def provider_profile(request, provider_id):
    """Shows detailed provider info, average rating, and reviews."""
    provider = get_object_or_404(ServiceProvider, id=provider_id)
    reviews = Review.objects.filter(provider=provider).order_by('-created_at')
    avg_rating_data = reviews.aggregate(Avg('rating'))
    avg_rating = avg_rating_data['rating__avg'] or 0

    context = {
        'provider': provider,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
    }
    return render(request, 'services/provider_profile.html', context)


# ==========================================
# BOOKING & DASHBOARD VIEWS
# ==========================================

@login_required
def create_booking(request, provider_id):
    provider = get_object_or_404(ServiceProvider, id=provider_id)
    if request.method == 'POST':
        service_date = request.POST.get('service_date')
        service_time = request.POST.get('service_time')
        description = request.POST.get('description')
        
        Booking.objects.create(
            user=request.user,
            provider=provider,
            service_date=service_date,
            service_time=service_time,
            description=description,
            status='pending'
        )
        messages.success(request, f"Request sent to {provider.user.get_full_name()}!")
        return redirect('my_bookings')
    return render(request, 'services/booking_form.html', {'provider': provider})

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'services/my_bookings.html', {'bookings': bookings})

@login_required
def provider_dashboard(request):
    try:
        provider = ServiceProvider.objects.get(user=request.user)
        bookings = Booking.objects.filter(provider=provider).order_by('-created_at')
        
        stats = {
            'total': bookings.count(),
            'pending': bookings.filter(status='pending').count(),
            'active': bookings.filter(status='confirmed').count(),
        }
        
        context = {
            'provider': provider,
            'bookings': bookings,
            'stats': stats,
        }
        return render(request, 'services/provider_dashboard.html', context)
    except ServiceProvider.DoesNotExist:
        messages.error(request, "You must be a registered provider to access this dashboard.")
        return redirect('home')

@login_required
def update_booking_status(request, booking_id, new_status):
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.provider.user == request.user:
        booking.status = new_status
        booking.save()
        messages.info(request, f"Status updated to {new_status}.")
    return redirect('provider_dashboard')


# ==========================================
# REVIEW & FEEDBACK VIEWS
# ==========================================

@login_required
def submit_review(request, booking_id):
    """Allows a customer to rate a provider after a service is completed."""
    # Safety: Ensure the booking belongs to the logged-in user
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if request.method == 'POST':
        # Create the review
        Review.objects.create(
            booking=booking,
            reviewer=request.user,
            provider=booking.provider,
            rating=int(request.POST.get('rating')),
            comment=request.POST.get('comment')
        )
        
        # Trigger the recommendation engine to update rankings
        update_all_scores()
        
        messages.success(request, 'Review submitted! Thank you for your feedback.')
        return redirect('my_bookings')
        
    return render(request, 'services/review_form.html', {'booking': booking})