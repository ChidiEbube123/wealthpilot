from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .forms import CustomUserCreationForm, UserProfileForm, RiskAssessmentForm
from .models import UserProfile, RiskAssessment, Portfolio, Investment
import random

def home(request):
    return render(request, 'main/home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Please complete your profile.')
            return redirect('risk_assessment')
    else:
        form = CustomUserCreationForm()
    return render(request, 'main/register.html', {'form': form})

@login_required
def risk_assessment(request):
    # Check if user already has a risk assessment
    try:
        risk_assessment = RiskAssessment.objects.get(user=request.user)
        return redirect('portfolio')
    except RiskAssessment.DoesNotExist:
        pass

    if request.method == 'POST':
        form = RiskAssessmentForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        
        if form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                # Save user profile
                profile = profile_form.save(commit=False)
                profile.user = request.user
                profile.save()
                
                # Calculate risk score
                market_volatility = int(request.POST.get('market_volatility', 3))
                investment_priority = int(request.POST.get('investment_priority', 3))
                
                # Simple risk scoring algorithm
                risk_score = (market_volatility + investment_priority) / 2
                time_horizon = form.cleaned_data['time_horizon']
                
                # Adjust for time horizon
                if time_horizon > 20:
                    risk_score += 1
                elif time_horizon > 10:
                    risk_score += 0.5
                elif time_horizon < 5:
                    risk_score -= 1
                
                # Determine risk tolerance
                if risk_score <= 2:
                    risk_tolerance = 'conservative'
                elif risk_score <= 3.5:
                    risk_tolerance = 'moderate'
                else:
                    risk_tolerance = 'aggressive'
                
                # Save risk assessment
                assessment = form.save(commit=False)
                assessment.user = request.user
                assessment.risk_tolerance = risk_tolerance
                assessment.risk_score = int(risk_score)
                assessment.save()
                
                # Generate portfolio
                generate_portfolio(request.user, risk_tolerance)
                
                messages.success(request, 'Risk assessment completed! Your portfolio has been generated.')
                return redirect('portfolio')
    else:
        form = RiskAssessmentForm()
        profile_form = UserProfileForm()
    
    return render(request, 'main/risk_assessment.html', {
        'form': form,
        'profile_form': profile_form
    })

def generate_portfolio(user, risk_tolerance):
    """Generate a portfolio based on risk tolerance"""
    portfolio_allocations = {
        'conservative': {
            'portfolio_type': 'conservative',
            'stocks_percentage': 30,
            'bonds_percentage': 50,
            'etfs_percentage': 15,
            'cash_percentage': 5,
            'expected_return': 5.5
        },
        'moderate': {
            'portfolio_type': 'balanced',
            'stocks_percentage': 50,
            'bonds_percentage': 30,
            'etfs_percentage': 15,
            'cash_percentage': 5,
            'expected_return': 7.2
        },
        'aggressive': {
            'portfolio_type': 'growth',
            'stocks_percentage': 70,
            'bonds_percentage': 15,
            'etfs_percentage': 12,
            'cash_percentage': 3,
            'expected_return': 9.1
        }
    }
    
    allocation = portfolio_allocations.get(risk_tolerance, portfolio_allocations['moderate'])
    
    Portfolio.objects.create(
        user=user,
        **allocation
    )
    
    # Generate sample investments
    sample_investments = [
        {'symbol': 'VTI', 'name': 'Vanguard Total Stock Market ETF', 'asset_type': 'etf'},
        {'symbol': 'BND', 'name': 'Vanguard Total Bond Market ETF', 'asset_type': 'bond'},
        {'symbol': 'AAPL', 'name': 'Apple Inc.', 'asset_type': 'stock'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'asset_type': 'stock'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'asset_type': 'stock'},
    ]
    
    for inv in sample_investments[:3]:  # Add 3 sample investments
        price = random.uniform(50, 300)
        Investment.objects.create(
            user=user,
            symbol=inv['symbol'],
            name=inv['name'],
            asset_type=inv['asset_type'],
            shares=random.uniform(1, 50),
            purchase_price=price,
            current_price=price * random.uniform(0.9, 1.1)  # Simulate price movement
        )

@login_required
def portfolio(request):
    try:
        portfolio = Portfolio.objects.get(user=request.user)
        investments = Investment.objects.filter(user=request.user)
        
        # Calculate total portfolio value
        total_value = sum(inv.total_value for inv in investments)
        total_gain_loss = sum(inv.gain_loss for inv in investments)
        
        context = {
            'portfolio': portfolio,
            'investments': investments,
            'total_value': total_value,
            'total_gain_loss': total_gain_loss,
        }
        return render(request, 'main/portfolio.html', context)
    except Portfolio.DoesNotExist:
        messages.info(request, 'Please complete your risk assessment first.')
        return redirect('risk_assessment')

@login_required
def dashboard(request):
    try:
        portfolio = Portfolio.objects.get(user=request.user)
        investments = Investment.objects.filter(user=request.user)
        risk_assessment = RiskAssessment.objects.get(user=request.user)
        
        # Calculate portfolio metrics
        total_value = sum(inv.total_value for inv in investments)
        total_gain_loss = sum(inv.gain_loss for inv in investments)
        
        # Asset allocation data for chart
        allocation_data = {
            'stocks': float(portfolio.stocks_percentage),
            'bonds': float(portfolio.bonds_percentage),
            'etfs': float(portfolio.etfs_percentage),
            'cash': float(portfolio.cash_percentage),
        }
        
        context = {
            'portfolio': portfolio,
            'investments': investments,
            'risk_assessment': risk_assessment,
            'total_value': total_value,
            'total_gain_loss': total_gain_loss,
            'allocation_data': allocation_data,
        }
        return render(request, 'main/dashboard.html', context)
    except (Portfolio.DoesNotExist, RiskAssessment.DoesNotExist):
        messages.info(request, 'Please complete your risk assessment first.')
        return redirect('risk_assessment')
