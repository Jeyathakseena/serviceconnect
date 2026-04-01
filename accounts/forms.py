from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, ServiceProvider

class UserRegisterForm(UserCreationForm):
    """
    Form for standard customers to register an account.
    """
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=20, required=False, label="Phone Number")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class ServiceProviderForm(forms.ModelForm):
    """
    Form for the professional details of a service provider.
    """
    # NEW: Allow users to type their own skill if not in the dropdown
    custom_category = forms.CharField(
        required=False, 
        label="Or add a new custom skill",
        help_text="Only fill this if your profession is not in the dropdown list above."
    )

    class Meta:
        model = ServiceProvider
        # ADDED custom_category to fields
        fields = ['service_category', 'custom_category', 'location', 'bio', 'experience_years', 'hourly_rate', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'experience_years': 'Years of Experience',
            'hourly_rate': 'Hourly Rate (₹)',
            'service_category': 'Select your Profession',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # DYNAMIC CATEGORIES: Scan database for all unique skills ever entered
        try:
            db_cats = ServiceProvider.objects.exclude(service_category='').values_list('service_category', flat=True).distinct()
        except Exception:
            db_cats = [] # Prevents error if database isn't migrated yet
            
        default_cats = ['plumber', 'electrician', 'cleaner', 'tutor', 'carpenter', 'painter', 'mechanic']
        all_cats = sorted(list(set(default_cats) | set(db_cats)))
        
        # Create choices for the dropdown
        choices = [('', '--- Select a category ---')] + [(cat.lower(), cat.title()) for cat in all_cats]
        self.fields['service_category'] = forms.ChoiceField(choices=choices, required=False)

        for field_name, field in self.fields.items():
            if field_name != 'profile_picture': 
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        """Logic to handle Custom Categories vs Dropdown Categories"""
        cleaned_data = super().clean()
        cat = cleaned_data.get('service_category')
        custom = cleaned_data.get('custom_category')

        if custom:
            # If they typed a custom skill, use that instead
            cleaned_data['service_category'] = custom.lower().strip()
        elif not cat:
            self.add_error('service_category', 'Please select a category or type a new custom skill.')
        
        return cleaned_data

# ==========================================
# NEW: PROFILE UPDATE FORMS
# ==========================================

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            
        self.fields['address'].widget.attrs.update({'rows': 3})

# Inherits all the dynamic category logic from ServiceProviderForm!
class ServiceProviderUpdateForm(ServiceProviderForm):
    pass