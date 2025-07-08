from django.urls import path
from .views import create_portfolio_view, dashboard_view, signup_view,risk_questionnaire_view

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('create/', create_portfolio_view, name='portfolio_form'),
    path('signup/', signup_view, name='signup'),
        path('questionnaire/', risk_questionnaire_view, name='risk_questionnaire'),

]

'''  path('buy/', views.buy_etf, name='buy_etf'),
    path('sell/', views.sell_etf, name='sell_etf'),'''