from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ServiceProvider

class UserRegisterForm(UserCreationForm):
    """
    Form for standard customers to register an account.
    Extends Django's built-in UserCreationForm to handle password creation safely.
    """
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    # This field will be saved to the UserProfile model later in the view
    phone = forms.CharField(max_length=20, required=False, label="Phone Number")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add the Bootstrap 'form-control' class to all fields automatically
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class ServiceProviderForm(forms.ModelForm):
    """
    Form for the professional details of a service provider.
    This will be used alongside the UserRegisterForm on the registration page.
    """
    class Meta:
        model = ServiceProvider
        fields = ['service_category', 'location', 'bio', 'experience_years', 'hourly_rate', 'profile_picture']
        
        # Customize the widgets and labels directly in the Meta class
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'experience_years': 'Years of Experience',
            'hourly_rate': 'Hourly Rate (₹)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add the Bootstrap 'form-control' class to all fields automatically
        for field_name, field in self.fields.items():
            # File inputs style better with standard form-control, but sometimes need custom handling. 
            # We'll apply the standard class to everything except the file upload for better cross-browser looks.
            if field_name != 'profile_picture': 
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-control' # Bootstrap 5 actually handles file inputs well with form-control