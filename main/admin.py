from django.contrib import admin
from .models import UserProfile, RiskAssessment, Portfolio, Investment

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'age', 'annual_income', 'investment_experience', 'created_at']
    list_filter = ['investment_experience', 'created_at']

@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'risk_tolerance', 'risk_score', 'time_horizon', 'created_at']
    list_filter = ['risk_tolerance', 'created_at']

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['user', 'portfolio_type', 'expected_return', 'created_at']
    list_filter = ['portfolio_type', 'created_at']

@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'symbol', 'name', 'asset_type', 'shares', 'current_price', 'purchase_date']
    list_filter = ['asset_type', 'purchase_date']
