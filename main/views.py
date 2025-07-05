from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .services import PortfolioService
from .models import PortfolioModel, AllocationModel
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
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
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'main/signup.html', {'form': form})
