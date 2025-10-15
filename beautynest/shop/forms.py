from django import forms
from .models import Review, Profile, Product
from .models import ContactMessage
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.forms import UserCreationForm

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['skin_type', 'age', 'about', 'avatar']

class ProductFilterForm(forms.Form):
    q = forms.CharField(required=False, label='Search')
    category = forms.ChoiceField(required=False, choices=[], label='Category')

    def __init__(self, *args, **kwargs):
        categories = kwargs.pop('categories', [])
        super().__init__(*args, **kwargs)
        self.fields['category'].choices = [('', 'All')] + [(c.id, c.name) for c in categories]

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        
class CustomSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")