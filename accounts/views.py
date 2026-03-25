from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, ServiceProviderForm
from .models import UserProfile, ServiceProvider

def register_user(request):
    """
    Handles registration for standard customers.
    """
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # Save the base User object
            user = form.save()
            
            # Extract the extra phone field and create the linked UserProfile
            phone = form.cleaned_data.get('phone')
            UserProfile.objects.create(user=user, phone=phone, is_provider=False)
            
            # Log the user in automatically
            login(request, user)
            
            # Send a success message to be displayed by base.html
            messages.success(request, f"Account created successfully! Welcome, {user.first_name}.")
            return redirect('home')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        # If it's a GET request, just show the empty form
        form = UserRegisterForm()
        
    return render(request, 'accounts/register.html', {'form': form})


def register_provider(request):
    """
    Handles registration for service providers using two combined forms.
    """
    if request.method == 'POST':
        # Instantiate BOTH forms with the submitted POST data and FILES (for the image)
        user_form = UserRegisterForm(request.POST)
        provider_form = ServiceProviderForm(request.POST, request.FILES)
        
        # Check if BOTH forms are valid before saving anything to the database
        if user_form.is_valid() and provider_form.is_valid():
            
            # 1. Save the base User object
            user = user_form.save()
            
            # 2. Extract the phone number and create the UserProfile (flagged as provider)
            phone = user_form.cleaned_data.get('phone')
            UserProfile.objects.create(user=user, phone=phone, is_provider=True)
            
            # 3. Save the ServiceProvider profile, but don't commit to the database yet...
            provider = provider_form.save(commit=False)
            # ...because we need to link it to the newly created user first!
            provider.user = user
            provider.save() # Now save it to the database
            
            # Log the provider in automatically
            login(request, user)
            
            messages.success(request, f"Provider account created successfully! Welcome to the team, {user.first_name}.")
            return redirect('home')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        # If it's a GET request, create empty versions of both forms
        user_form = UserRegisterForm()
        provider_form = ServiceProviderForm()
        
    # Pass BOTH forms to the template
    context = {
        'user_form': user_form,
        'provider_form': provider_form
    }
    return render(request, 'accounts/register_provider.html', context)


@login_required
def profile(request):
    """
    A simple view to show the logged-in user their own information.
    The @login_required decorator strictly prevents non-logged-in users from seeing this.
    """
    return render(request, 'accounts/profile.html')