import math
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from accounts.models import ServiceProvider
from .models import Review, Booking
from .utils import update_all_scores 

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

# NEW: Helper function to get all skills for search dropdowns dynamically
def get_dynamic_categories():
    try:
        db_cats = ServiceProvider.objects.exclude(service_category='').values_list('service_category', flat=True).distinct()
    except Exception:
        db_cats = []
    default_cats = ['plumber', 'electrician', 'cleaner', 'tutor', 'carpenter', 'painter', 'mechanic']
    all_cats = sorted(list(set(default_cats) | set(db_cats)))
    return [(cat.lower(), cat.title()) for cat in all_cats]

# ==========================================
# DISCOVERY & SEARCH VIEWS
# ==========================================

def homepage(request):
    top_providers = ServiceProvider.objects.all().order_by('-recommendation_score')[:6]
    context = {
        'top_providers': top_providers,
        'SERVICE_CATEGORIES': get_dynamic_categories(), # CHANGED HERE
    }
    return render(request, 'services/home.html', context)

def search_providers(request):
    category_query = request.GET.get('category', '')
    location_query = request.GET.get('location', '')
    filter_by = request.GET.get('filter_by', '')
    
    user_lat = request.GET.get('user_lat')
    user_lng = request.GET.get('user_lng')

    providers = ServiceProvider.objects.all()

    if category_query:
        providers = providers.filter(service_category=category_query)
    
    if location_query and not (user_lat and user_lng):
        providers = providers.filter(location__icontains=location_query)

    if "top_rated" in filter_by:
        providers = providers.annotate(avg_rating=Avg('received_reviews__rating'))

    providers_list = list(providers)

    if "nearby" in filter_by:
        if user_lat and user_lng:
            try:
                u_lat, u_lng = float(user_lat), float(user_lng)
                for p in providers_list:
                    if p.latitude is not None and p.longitude is not None:
                        p.distance_km = round(haversine(u_lat, u_lng, p.latitude, p.longitude), 1)
                    else:
                        p.distance_km = None
                
                if filter_by == "nearby_top_rated":
                    providers_list.sort(key=lambda x: (x.distance_km is None, x.distance_km, -(x.avg_rating or 0)))
                else:
                    providers_list.sort(key=lambda x: (x.distance_km is None, x.distance_km))
            except (ValueError, TypeError):
                pass
    elif filter_by == "top_rated":
        providers_list.sort(key=lambda x: (getattr(x, 'avg_rating', None) is None, -(getattr(x, 'avg_rating', 0) or 0)))
    else:
        providers_list.sort(key=lambda x: -x.recommendation_score)

    context = {
        'providers': providers_list,
        'category': category_query,
        'location': location_query,
        'filter_by': filter_by,
        'user_lat': user_lat,
        'user_lng': user_lng,
        'SERVICE_CATEGORIES': get_dynamic_categories(), # CHANGED HERE
    }
    return render(request, 'services/search_results.html', context)

def provider_profile(request, provider_id):
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
# (These remain exactly the same as your code)

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

@login_required
def submit_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if request.method == 'POST':
        Review.objects.create(
            booking=booking,
            reviewer=request.user,
            provider=booking.provider,
            rating=int(request.POST.get('rating')),
            comment=request.POST.get('comment')
        )
        update_all_scores()
        messages.success(request, 'Review submitted! Thank you for your feedback.')
        return redirect('my_bookings')
        
    return render(request, 'services/review_form.html', {'booking': booking})