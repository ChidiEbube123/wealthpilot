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
    def __str__(self):
        return self.user.username

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
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    tolerance_score = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    capacity_score = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_score = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def calculate_scores(self):
        """Calculate weighted scores for tolerance and capacity"""
        user_answers = self.user_answers.select_related('question', 'selected_answer')
        
        tolerance_total = 0
        tolerance_weight = 0
        capacity_total = 0
        capacity_weight = 0
        
        for user_answer in user_answers:
            question = user_answer.question
            answer_value = user_answer.selected_answer.answer_value
            weighted_value = answer_value * question.question_weight
            
            if question.question_type == 'Tolerance':
                tolerance_total += weighted_value
                tolerance_weight += question.question_weight
            elif question.question_type == 'Capacity':
                capacity_total += weighted_value
                capacity_weight += question.question_weight
        
        # Calculate average scores
        self.tolerance_score = tolerance_total / tolerance_weight if tolerance_weight > 0 else 0
        self.capacity_score = capacity_total / capacity_weight if capacity_weight > 0 else 0
        
        # Overall score (you can adjust this formula)
        self.total_score = (self.tolerance_score + self.capacity_score) / 2
        
        self.save()
    
    def get_risk_profile(self):
        """Return risk profile based on total score"""
        if not self.total_score:
            return "Not assessed"
        
        if self.total_score >= 3.5:
            return "High Risk"
        elif self.total_score >= 2.5:
            return "Moderate Risk"
        elif self.total_score >= 1.5:
            return "Low-Moderate Risk"
        else:
            return "Conservative"
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d')} - {self.get_risk_profile()}"


class RiskQuestion(models.Model):
    QUESTION_TYPES = [
        ('Tolerance', 'Risk Tolerance'),
        ('Capacity', 'Risk Capacity'),
    ]
    
    question_id = models.IntegerField(unique=True)  
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    question_weight = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        ordering = ['question_id']
    
    def __str__(self):
        return f"Q{self.question_id}: {self.question_text[:50]}..."
    
class RiskAnswer(models.Model):
    answer_id = models.IntegerField(unique=True)  
    answer_text = models.CharField(max_length=200)
    answer_value = models.IntegerField() 
    question = models.ForeignKey(RiskQuestion, on_delete=models.CASCADE, related_name='answers')
    
    class Meta:
        ordering = ['answer_value']
    
    def __str__(self):
        return f"{self.answer_text} (Value: {self.answer_value})"
    
class UserAnswer(models.Model):
    assessment = models.ForeignKey(RiskProfile, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(RiskQuestion, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(RiskAnswer, on_delete=models.CASCADE)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['assessment', 'question']
    
    def __str__(self):
        return f"{self.assessment.user.username} - Q{self.question.question_id}: {self.selected_answer.answer_text}"