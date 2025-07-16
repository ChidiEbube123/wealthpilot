from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .services import PortfolioService
from .models import PortfolioModel,RiskProfile, AllocationModel,UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import RiskQuestion, RiskAnswer, RiskProfile, UserAnswer
import json
@login_required
def home_view(request):
    portfolio=UserProfile.objects.filter(user= request.answer)
    #Pause
    
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
            return redirect('risk_assessment_start')
    else:
        form = UserCreationForm()
    return render(request, 'main/signup.html', {'form': form})

def risk_questionnaire_view(request,assessment_id):
    assessment = get_object_or_404(RiskProfile, id=assessment_id, user=request.user)
    
    if assessment.completed:
        return redirect('risk_assessment_results', assessment_id=assessment.id)
    
    # Get all questions ordered by ID
    questions = RiskQuestion.objects.prefetch_related('answers').order_by('question_id')
    
    # Get user's existing answers
    existing_answers = {}
    for user_answer in assessment.user_answers.select_related('selected_answer'):
        existing_answers[user_answer.question_id] = user_answer.selected_answer.answer_id
    
    if request.method == 'POST':
        # Process form submission
        all_answered = True
        
        for question in questions:
            answer_id = request.POST.get(f'question_{question.question_id}')
            
            if answer_id:
                try:
                    selected_answer = RiskAnswer.objects.get(
                        answer_id=answer_id,
                        question=question
                    )
                    
                    # Create or update user answer
                    UserAnswer.objects.update_or_create(
                        assessment=assessment,
                        question=question,
                        defaults={'selected_answer': selected_answer}
                    )
                    
                except RiskAnswer.DoesNotExist:
                    messages.error(request, f'Invalid answer selected for question {question.question_id}')
                    all_answered = False
            else:
                all_answered = False
        
        if all_answered:
            # Calculate scores and mark as completed
            assessment.calculate_scores()
            assessment.completed = True
            portfolio_id = PortfolioService.get_portfolio_id(assessment.tolerance_score, assessment.capacity_score)
            
            tickers = get_tickers_by_risk(assessment.tolerance_score,assessment.capacity_score)[0]  # you can customize this
            expected_return = 0.001
            portfolio=PortfolioModel.objects.get_or_create(id=portfolio_id,defaults={'name':f"porfolio{portfolio_id}",'risk_bucket':assessment.total_score ,'expected_return':expected_return})#Not necessarrily the best            service = PortfolioService(tickers, expected_return).create()
            user_profile=UserProfile.objects.get_or_create(user=request.user)
            user_profile[0].portfolio=portfolio[0]
            user_profile[0].save()
            assessment.save()
            
            messages.success(request, 'Risk assessment completed successfully!')

            return redirect('risk_assessment_results', assessment_id=assessment.id)
        else:
            messages.error(request, 'Please answer all questions before submitting.')
    total_questions = questions.count()
    answered_questions = len(existing_answers)
    progress_percentage = (answered_questions / total_questions * 100) if total_questions > 0 else 0
    
    context = {
        'assessment': assessment,
        'questions': questions,
        'existing_answers': existing_answers,
        'progress_percentage': progress_percentage,
        'total_questions': total_questions,
        'answered_questions': answered_questions,
    }
    
    return render(request, 'main/risk_questionnaire.html', context)

def risk_assessment_start(request):
    """Start a new risk assessment"""
    # Check if user has incomplete assessment
    incomplete_assessment = RiskProfile.objects.filter(
        user=request.user, 
        completed=False
    ).first()
    
    if incomplete_assessment:
        return redirect('risk_assessment_continue', assessment_id=incomplete_assessment.id)
    
    # Create new assessment
    assessment = RiskProfile.objects.create(user=request.user)
    return redirect('risk_assessment_continue', assessment_id=assessment.id)

@login_required
def risk_assessment_results(request, assessment_id):
    """Display risk assessment results"""
    assessment = get_object_or_404(
        RiskProfile, 
        id=assessment_id, 
        user=request.user,
        completed=True
    )
    
    # Get user answers with related data
    user_answers = assessment.user_answers.select_related(
        'question', 'selected_answer'
    ).order_by('question__question_id')
    
    # Separate answers by question type
    tolerance_answers = []
    capacity_answers = []
    
    for user_answer in user_answers:
        if user_answer.question.question_type == 'Tolerance':
            tolerance_answers.append(user_answer)
        else:
            capacity_answers.append(user_answer)
    context = {
        'assessment': assessment,
        'tolerance_answers': tolerance_answers,
        'capacity_answers': capacity_answers,
 
    }
    
    return render(request, 'main/results.html', context)

def get_tickers_by_risk(tolerance, capacity):
    if tolerance < 5:
        return "AGG SHY GLD", 0.0003  # Very conservative
    elif tolerance < 10:
        return "BND IEI TIP", 0.0005  # Conservative
    elif tolerance < 15:
        return "VTI VNQ GLD", 0.0009  # Moderate
    else:
        return "VTI QQQ DBC", 0.0012  # Aggressive