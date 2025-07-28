from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(validators=[MinValueValidator(18), MaxValueValidator(100)])
    annual_income = models.DecimalField(max_digits=12, decimal_places=2)
    investment_experience = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class RiskAssessment(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    risk_tolerance = models.CharField(max_length=20, choices=[
        ('conservative', 'Conservative'),
        ('moderate', 'Moderate'),
        ('aggressive', 'Aggressive'),
    ])
    time_horizon = models.IntegerField(help_text="Investment time horizon in years")
    financial_goals = models.TextField()
    risk_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Risk Assessment"

class Portfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    portfolio_type = models.CharField(max_length=20, choices=[
        ('conservative', 'Conservative'),
        ('balanced', 'Balanced'),
        ('growth', 'Growth'),
        ('aggressive', 'Aggressive Growth'),
    ])
    stocks_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    bonds_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    etfs_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    cash_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    expected_return = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Portfolio"

class Investment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=20, choices=[
        ('stock', 'Stock'),
        ('bond', 'Bond'),
        ('etf', 'ETF'),
        ('cash', 'Cash'),
    ])
    shares = models.DecimalField(max_digits=10, decimal_places=4)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.symbol} - {self.user.username}"

    @property
    def total_value(self):
        return self.shares * self.current_price

    @property
    def gain_loss(self):
        return (self.current_price - self.purchase_price) * self.shares

    @property
    def gain_loss_percentage(self):
        if self.purchase_price > 0:
            return ((self.current_price - self.purchase_price) / self.purchase_price) * 100
        return 0
