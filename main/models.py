from django.db import models
from django.contrib.auth.models import User


class PortfolioModel(models.Model):
    name = models.CharField(max_length=50)
    id=models.CharField(max_length=5, unique=True,primary_key=True)
    risk_bucket = models.IntegerField()
    expected_return = models.FloatField()
    expected_risk = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(default=10000.00, max_digits=12, decimal_places=2)
    portfolio=models.ForeignKey(PortfolioModel,null=True, on_delete=models.CASCADE)



class AllocationModel(models.Model):
    portfolio = models.ForeignKey(PortfolioModel, related_name='allocations', on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    percentage = models.FloatField()


class Transaction(models.Model):
    TRANSACTION_TYPE = (
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    etf_symbol = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPE)
    timestamp = models.DateTimeField(auto_now_add=True)



class RiskProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tolerance = models.IntegerField(null=True)
    capacity = models.IntegerField(null=True)
    completed = models.BooleanField(default=False)