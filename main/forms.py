from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, RiskAssessment

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['age', 'annual_income', 'investment_experience']
        widgets = {
            'annual_income': forms.NumberInput(attrs={'step': '0.01'}),
        }

class RiskAssessmentForm(forms.ModelForm):
    # Additional questions for risk assessment
    market_volatility = forms.ChoiceField(
        choices=[
            (1, 'Very uncomfortable - I would sell immediately'),
            (2, 'Uncomfortable - I would consider selling'),
            (3, 'Neutral - I would hold my investments'),
            (4, 'Comfortable - I would consider buying more'),
            (5, 'Very comfortable - I would definitely buy more'),
        ],
        widget=forms.RadioSelect,
        label="How would you react to a 20% market decline?"
    )
    
    investment_priority = forms.ChoiceField(
        choices=[
            (1, 'Preserve capital - avoid losses'),
            (2, 'Generate income - steady returns'),
            (3, 'Balanced - moderate growth with some income'),
            (4, 'Growth - maximize long-term returns'),
            (5, 'Aggressive growth - maximum returns regardless of risk'),
        ],
        widget=forms.RadioSelect,
        label="What is your primary investment priority?"
    )

    class Meta:
        model = RiskAssessment
        fields = ['time_horizon', 'financial_goals']
        widgets = {
            'financial_goals': forms.Textarea(attrs={'rows': 4}),
        }