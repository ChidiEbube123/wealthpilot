from django.urls import path
from .views import create_portfolio_view, dashboard_view, signup_view,risk_questionnaire_view,home_view,risk_assessment_start,risk_assessment_results

urlpatterns = [
    path('', home_view, name='dashboard'),
    path('create/', create_portfolio_view, name='portfolio_form'),
    path('signup/', signup_view, name='signup'),
           path('assessment/start/', risk_assessment_start, name='risk_assessment_start'),
    path('assessment/<int:assessment_id>/continue/', risk_questionnaire_view, name='risk_assessment_continue'),
    path('assessment/<int:assessment_id>/results/', risk_assessment_results, name='risk_assessment_results'),

]

'''  path('buy/', views.buy_etf, name='buy_etf'),
    path('sell/', views.sell_etf, name='sell_etf'),'''