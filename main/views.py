from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .services import PortfolioService
from .models import PortfolioModel,RiskProfile, AllocationModel,UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .forms import RiskProfileForm

@login_required
def create_portfolio_view(request):
    if request.method == "POST":
        tickers = request.POST['tickers']
        expected_return = float(request.POST['expected_return'])
        name = request.POST['name']
        risk_bucket = int(request.POST['risk_bucket'])

        service = PortfolioService(tickers, expected_return).create()

        portfolio = PortfolioModel.objects.create(
            user=request.user,
            name=name,
            risk_bucket=risk_bucket,
            expected_return=expected_return,
            expected_risk=service.expected_risk
        )

        for alloc in service.allocations:
            AllocationModel.objects.create(
                portfolio=portfolio,
                ticker=alloc["ticker"],
                percentage=alloc["percentage"]
            )

        return redirect('dashboard')

    return render(request, 'main/form.html')

@login_required
def dashboard_view(request):
    portfolios = PortfolioModel.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'main/dashboard.html', {'portfolios': portfolios})

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('risk_questionnaire')
    else:
        form = UserCreationForm()
    return render(request, 'main/signup.html', {'form': form})

def risk_questionnaire_view(request):
    if request.method == 'POST':
        form = RiskProfileForm(request.POST)
        if form.is_valid():
            profile = RiskProfile.objects.get_or_create(user=request.user)
            profile[0].tolerance = form.cleaned_data['tolerance']
            profile[0].capacity = form.cleaned_data['capacity']
            profile[0].completed = True
            profile[0].save()
            # SHould not generate should match
            # generate portfolio
            portfolio_id = PortfolioService.get_portfolio_id(profile[0].tolerance, profile[0].capacity)
            tickers = "VTI TLT IEI GLD DBC"  # you can customize this
            expected_return = 0.001
            portfolio=PortfolioModel.objects.get_or_create(id=portfolio_id)
            service = PortfolioService(tickers, expected_return).create()
            user_profile=UserProfile.objects.get_or_create(user=request.user)
            user_profile[0].portfolio=portfolio[0]
            user_profile[0].save()


#            for alloc in service.allocations:
#                AllocationModel.objects.create(
#                    portfolio=portfolio,
#                    ticker=alloc["ticker"],
#                   percentage=alloc["percentage"]
#                )

            return redirect('dashboard')
    else:
        form = RiskProfileForm()

    return render(request, 'main/risk_questionnaire.html', {'form': form})
