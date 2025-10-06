from django import forms
from .models import Author

class ProfileEditForm(forms.Form):
    """Form for editing author profile information"""
    
    display_name = forms.CharField(
        max_length=39,
        required=True,
        label='Display Name',
        widget=forms.TextInput(attrs={
            'placeholder': 'Your display name'
        })
    )
    
    github = forms.URLField(
        required=False,
        label='GitHub URL',
        widget=forms.URLInput(attrs={
            'placeholder': 'https://github.com/yourusername'
        })
    )
    
    profile_image = forms.URLField(
        required=False,
        label='Profile Image URL',
        widget=forms.URLInput(attrs={
            'placeholder': 'https://example.com/image.jpg'
        })
    )
    
    def clean_github(self):
        """Validate GitHub URL format"""
        github = self.cleaned_data.get('github')
        if github and not github.startswith('http'):
            raise forms.ValidationError('Please enter a valid URL starting with http:// or https://')
        return github
    
    def clean_profile_image(self):
        """Validate profile image URL format"""
        profile_image = self.cleaned_data.get('profile_image')
        if profile_image and not profile_image.startswith('http'):
            raise forms.ValidationError('Please enter a valid URL starting with http:// or https://')
        return profile_image