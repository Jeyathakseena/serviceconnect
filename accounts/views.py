import json
import urllib.request
import urllib.parse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, ServiceProviderForm
from .models import UserProfile, ServiceProvider

def geocode_city(city_name):
    """
    Helper to convert city name to Lat/Lng using OSM Nominatim.
    Returns (lat, lng) or (None, None) on failure.
    """
    try:
        # Encode the city name for a URL (e.g., 'New York' -> 'New%20York')
        encoded_city = urllib.parse.quote(city_name)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_city}&format=json&limit=1"
        
        # Nominatim REQUIRES a User-Agent or it returns 403 Forbidden
        headers = {'User-Agent': 'ServiceConnect/1.0'}
        req = urllib.request.Request(url, headers=headers)
        
        # Call API with a 5-second timeout
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return lat, lon
    except Exception as e:
        # Silently catch errors (Network down, timeout, etc.) to prevent crash
        print(f"Geocoding error: {e}")
        
    return None, None

def register_user(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            phone = form.cleaned_data.get('phone')
            UserProfile.objects.create(user=user, phone=phone, is_provider=False)
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome, {user.first_name}.")
            return redirect('home')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def register_provider(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        provider_form = ServiceProviderForm(request.POST, request.FILES)
        
        if user_form.is_valid() and provider_form.is_valid():
            user = user_form.save()
            phone = user_form.cleaned_data.get('phone')
            UserProfile.objects.create(user=user, phone=phone, is_provider=True)
            
            provider = provider_form.save(commit=False)
            provider.user = user
            
            # --- GEOLOCATION LOGIC ---
            city_name = provider_form.cleaned_data.get('location')
            lat, lng = geocode_city(city_name)
            provider.latitude = lat
            provider.longitude = lng
            provider.save() 

            login(request, user)
            
            # Dynamic success message based on geocoding result
            success_msg = f"Provider account created successfully! Welcome, {user.first_name}."
            if lat:
                success_msg += " Your location has been mapped successfully."
            else:
                success_msg += " Note: We could not detect your exact location. You can update it from your profile."
            
            messages.success(request, success_msg)
            return redirect('home')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        user_form = UserRegisterForm()
        provider_form = ServiceProviderForm()
        
    return render(request, 'accounts/register_provider.html', {
        'user_form': user_form, 
        'provider_form': provider_form
    })

@login_required
def profile(request):
    return render(request, 'accounts/profile.html')