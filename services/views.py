import math
import json
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from django.conf import settings

from accounts.models import ServiceProvider
from .models import Review, Booking, EmergencyJob
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
        'SERVICE_CATEGORIES': get_dynamic_categories(), 
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
        'SERVICE_CATEGORIES': get_dynamic_categories(), 
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

@login_required
def create_booking(request, provider_id):
    provider = get_object_or_404(ServiceProvider, id=provider_id)

    if request.user == provider.user:
        messages.error(request, "You cannot book your own services!")
        return redirect('provider_profile', provider_id=provider.id)

    if request.method == 'POST':
        service_date = request.POST.get('service_date')
        service_time = request.POST.get('service_time')
        description = request.POST.get('description')
        address = request.POST.get('address')
        lat = request.POST.get('lat')
        lng = request.POST.get('lng')
        
        # NEW SECURITY CHECK: Prevent Double Booking
        overlap_exists = Booking.objects.filter(
            provider=provider,
            service_date=service_date,
            service_time=service_time,
            status='confirmed'
        ).exists()

        if overlap_exists:
            messages.error(request, "This professional already has a confirmed booking at that exact date and time. Please select a different slot.")
            return redirect('provider_profile', provider_id=provider.id)
        
        Booking.objects.create(
            user=request.user,
            provider=provider,
            service_date=service_date,
            service_time=service_time,
            address=address,
            latitude=float(lat) if lat else None,
            longitude=float(lng) if lng else None,
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
    
    # SAFETY CHECK: If a review already exists for this booking, prevent duplicate submission
    if hasattr(booking, 'review'):
        messages.warning(request, "You have already left a review for this booking!")
        return redirect('my_bookings')
    
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

# ==========================================
# EMERGENCY SOS SYSTEM
# ==========================================

@login_required
def trigger_emergency(request):
    if request.method == 'POST':
        category = request.POST.get('emergency_category', '').strip().lower()
        
        # FIXED: Properly capture and format the custom category
        if category == 'other':
            custom = request.POST.get('custom_category', '').strip().lower()
            if custom:
                category = custom
            
        lat = request.POST.get('user_lat')
        lng = request.POST.get('user_lng')

        # Safety check: We can't dispatch without a location
        if not lat or not lng:
            messages.error(request, "Emergency Dispatch requires your exact location. Please allow location access.")
            return redirect('home')

        # Drop the SOS Beacon into the database
        emergency = EmergencyJob.objects.create(
            customer=request.user,
            service_category=category,
            latitude=float(lat),
            longitude=float(lng),
            status='searching'
        )
        
        # Send them to the waiting radar screen
        return redirect('emergency_radar', emergency_id=emergency.id)
        
    return redirect('home')

@login_required
def emergency_radar(request, emergency_id):
    emergency = get_object_or_404(EmergencyJob, id=emergency_id, customer=request.user)
    
    # If a provider has already accepted it, redirect to a success page
    if emergency.status == 'accepted':
        messages.success(request, f"Help is on the way! {emergency.accepted_by.user.get_full_name()} has accepted your SOS.")
        return redirect('my_bookings')
        
    return render(request, 'services/emergency_radar.html', {'emergency': emergency})

# NEW: Allow users to cancel their active broadcast
@login_required
def cancel_emergency(request, emergency_id):
    if request.method == 'POST':
        emergency = get_object_or_404(EmergencyJob, id=emergency_id, customer=request.user)
        if emergency.status == 'searching':
            # Setting it to cancelled removes it from all provider radars instantly
            emergency.status = 'cancelled' 
            emergency.save()
            messages.info(request, "Your SOS Broadcast has been safely cancelled.")
        else:
            messages.warning(request, "Too late! A professional has already accepted your request.")
    return redirect('home')

@login_required
def check_emergencies(request):
    """ API Endpoint: Checks if this provider is in the Top 10 closest for any active emergency """
    try:
        provider = ServiceProvider.objects.get(user=request.user)
    except ServiceProvider.DoesNotExist:
        return JsonResponse({'emergencies': []}) # Not a provider
        
    if not provider.latitude or not provider.longitude:
        return JsonResponse({'emergencies': []}) # Cannot dispatch to providers without a location

    # 1. Housekeeping: Auto-expire emergencies older than 10 minutes
    ten_mins_ago = timezone.now() - timedelta(minutes=10)
    EmergencyJob.objects.filter(status='searching', created_at__lt=ten_mins_ago).update(status='expired')

    # 2. Find active emergencies
    active_emergencies = EmergencyJob.objects.filter(status='searching')
    
    my_alerts = []
    for emergency in active_emergencies:
        em_cat = emergency.service_category.lower()
        prov_cat = provider.service_category.lower()

        # FIXED: Only notify if categories match EXACTLY, or if it's a blank "other" emergency
        if em_cat != 'other' and em_cat != prov_cat:
            continue 

        # 3. The Math: Find all eligible providers and calculate their distances
        if em_cat == 'other':
            # If user left it totally blank, ping everyone
            all_eligible = ServiceProvider.objects.exclude(latitude__isnull=True)
        else:
            # Case insensitive exact match for their typed category (e.g., tutors)
            all_eligible = ServiceProvider.objects.filter(service_category__iexact=em_cat).exclude(latitude__isnull=True)
        
        provider_distances = []
        for p in all_eligible:
            dist = haversine(emergency.latitude, emergency.longitude, p.latitude, p.longitude)
            if dist <= 30.0:
                provider_distances.append((dist, p.id))
        
        # Sort by closest distance and slice the top 10!
        provider_distances.sort(key=lambda x: x[0])
        top_10_ids = [pd[1] for pd in provider_distances[:10]]

        # 4. If this provider is in the Top 10, send the alert!
        if provider.id in top_10_ids:
            my_distance = next(pd[0] for pd in provider_distances if pd[1] == provider.id)
            time_ago = int((timezone.now() - emergency.created_at).total_seconds() / 60)
            
            my_alerts.append({
                'id': emergency.id,
                'category': emergency.service_category.title() if emergency.service_category != 'other' else 'General Emergency',
                'distance': round(my_distance, 1),
                'time_ago': time_ago
            })

    return JsonResponse({'emergencies': my_alerts})

@login_required
def accept_emergency(request, emergency_id):
    """ Handles the race condition when a provider clicks Accept """
    if request.method == 'POST':
        try:
            provider = ServiceProvider.objects.get(user=request.user)
            emergency = get_object_or_404(EmergencyJob, id=emergency_id)

            # Check if it is still available
            if emergency.status == 'searching':
                emergency.status = 'accepted'
                emergency.accepted_by = provider
                emergency.save()
                
                # Automatically create a confirmed booking for their dashboard!
                Booking.objects.create(
                    user=emergency.customer,
                    provider=provider,
                    service_date=timezone.now().date(),
                    service_time=timezone.now().time(),
                    description=f"EMERGENCY SOS DISPATCH: {emergency.service_category.title()}",
                    address="EMERGENCY SOS: Customer Location pinned via GPS",
                    latitude=emergency.latitude,
                    longitude=emergency.longitude,
                    status='confirmed'
                )
                messages.success(request, f"SOS Accepted! You are now dispatched to help {emergency.customer.first_name}.")
            else:
                messages.error(request, "Too slow! Another professional just claimed this emergency or it was cancelled.")
        except ServiceProvider.DoesNotExist:
            pass
            
    return redirect('provider_dashboard')

# ==========================================
# AI SUPPORT CHATBOT
# ==========================================

from google import genai
from google.api_core import exceptions as errors

SYSTEM_INSTRUCTION = """
# ROLE & IDENTITY
You are the official "ServiceConnect Support Bot." Your exclusive purpose is to assist BOTH Customers and Service Providers in using the ServiceConnect platform.

# KNOWLEDGE DOMAIN
Your knowledge is strictly limited to the following platform features:

**For Customers:**
1. HOW TO BOOK: Explain searching for providers, clicking "Book Now," selecting dates, and using the GPS button to pin their exact address.
2. EMERGENCY SOS: Explain the red SOS button. It broadcasts their live GPS coordinates to providers within a 30km radius for a rapid 10-minute dispatch.
3. SERVICE CATEGORIES: We offer Plumbers, Electricians, Cleaners, Tutors, Carpenters, Painters, Mechanics, AND "Custom Services" (users can select 'Other' and type their specific, unique problem).
4. PRICING: Basic service consultation visits start at ₹200.

**For Service Providers:**
1. DASHBOARD MANAGEMENT: Explain how to check the dashboard for Pending, Active, and Total bookings.
2. ACCEPTING JOBS & NAVIGATION: Explain that they must click "Accept Job" to reveal the customer's exact address. Once accepted, a "Navigate" button appears that opens Google Maps.
3. SOS ALERTS: Explain that their dashboard will flash a red alert and their mobile phone will physically vibrate if a nearby SOS is triggered. They must accept it quickly before the 10-minute timer expires or another provider claims the job.

**General Platform Info:**
- LOCATION: We proudly serve in Tamil Nadu.
- CONTACT: For deep technical glitches, direct users to email support@serviceconnect.com.

# STRICT GUARDRAILS (THE RED LINES)
1. REFUSAL RULE: If a user asks about ANY topic not directly related to ServiceConnect (e.g., cooking, coding, writing stories, politics, history, general trivia), you MUST politely but firmly refuse. 
   - *Example Refusal:* "I'm strictly wired for ServiceConnect duties. I can't help with that"
2. NO HALLUCINATION: If you do not know the exact answer regarding the website's functionality, do not guess or make up features. Provide the support email.
3. TASK BOUNDARIES: Do not write code, do not write essays, and do not generate off-topic creative content under any circumstances.

# TONE & STYLE
- Professional, Polite, Short and sweet give the exact answer.
- Concise (Keep answers under 3 sentences).
- Include a warm touch of South Indian hospitality where it feels natural (e.g., "Vanakkam!").
"""

import os
from django.conf import settings
from django.http import JsonResponse
from google import genai  # Ensure this matches your installation
from dotenv import load_dotenv

# Load .env variables at the top of the file
load_dotenv()

def chatbot_api(request):
    """ Handles AJAX requests from the floating chat window """
    if request.method == "POST":
        user_message = request.POST.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'reply': "Please type a message."})

        # 1. Get the API Key from settings
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            return JsonResponse({'reply': "I'm offline (API Key missing). Please check settings!"})

        # 2. Build the full prompt with your system instructions
        full_prompt = f"{SYSTEM_INSTRUCTION}\n\nUser Question: {user_message}"

        try:
            # 3. Initialize the Client
            client = genai.Client(api_key=api_key)
            
            # 4. Generate content using the stable model name
            # Note: Using 'gemini-1.5-flash' or 'gemini-2.0-flash' is the safest for live demos
            response = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=full_prompt
            )
            
            # 5. Check if the response actually contains text
            if response and hasattr(response, 'text') and response.text:
                return JsonResponse({'reply': response.text})
            else:
                return JsonResponse({'reply': "Vanakkam! I'm sorry, I can't answer that specific question. Try asking about our services!"})
            
        except Exception as e:
            # THIS IS THE CRITICAL PART: 
            # It catches the 500 error and sends a polite message instead of crashing.
            print(f"DEBUG AI ERROR: {e}") 
            return JsonResponse({'reply': "Vanakkam! I'm handling many requests right now. Please try again in 10 seconds!"})
            
    return JsonResponse({'error': 'Invalid request'}, status=400)