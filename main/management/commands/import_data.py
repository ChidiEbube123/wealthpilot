# management/commands/import_risk_data.py
from django.core.management.base import BaseCommand
import pandas as pd
from main.models import RiskQuestion, RiskAnswer
import os

class Command(BaseCommand):
    help = 'Import risk assessment data from CSV files'
    
    def add_arguments(self, parser):
        parser.add_argument('--questions', type=str, help='Path to Risk Questions.csv file')
        parser.add_argument('--answers', type=str, help='Path to Risk Answers.csv file')
        parser.add_argument('--clear', action='store_true', help='Clear existing data first')
    
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            RiskAnswer.objects.all().delete()
            RiskQuestion.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared!'))
        
        # Import questions first
        if options['questions']:
            self.import_questions(options['questions'])
        
        # Import answers
        if options['answers']:
            self.import_answers(options['answers'])
    
    def import_questions(self, file_path):
        self.stdout.write(f'Importing questions from {file_path}...')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        
        try:
            df = pd.read_csv(file_path)
            
            # Validate required columns
            required_columns = ['QuestionID', 'QuestionType', 'QuestionText', 'QuestionWeight']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.stdout.write(
                    self.style.ERROR(f'Missing columns: {missing_columns}')
                )
                return
            
            created_count = 0
            updated_count = 0
            
            for _, row in df.iterrows():
                question, created = RiskQuestion.objects.update_or_create(
                    question_id=row['QuestionID'],
                    defaults={
                        'question_type': row['QuestionType'],
                        'question_text': row['QuestionText'],
                        'question_weight': row['QuestionWeight']
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'Created: Q{question.question_id} - {question.question_text[:50]}...')
                else:
                    updated_count += 1
                    self.stdout.write(f'Updated: Q{question.question_id} - {question.question_text[:50]}...')
            
            self.stdout.write(
                self.style.SUCCESS(f'Questions imported! Created: {created_count}, Updated: {updated_count}')
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing questions: {str(e)}'))
    
    def import_answers(self, file_path):
        self.stdout.write(f'Importing answers from {file_path}...')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        
        try:
            df = pd.read_csv(file_path)
            
            # Validate required columns
            required_columns = ['AnswerID', 'AnswerText', 'AnswerValue', 'QuestionID']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.stdout.write(
                    self.style.ERROR(f'Missing columns: {missing_columns}')
                )
                return
            
            created_count = 0
            updated_count = 0
            error_count = 0
            
            for _, row in df.iterrows():
                try:
                    # Find the corresponding question
                    question = RiskQuestion.objects.get(question_id=row['QuestionID'])
                    
                    answer, created = RiskAnswer.objects.update_or_create(
                        answer_id=row['AnswerID'],
                        defaults={
                            'answer_text': row['AnswerText'],
                            'answer_value': row['AnswerValue'],
                            'question': question
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f'Created: {answer.answer_text} (Value: {answer.answer_value})')
                    else:
                        updated_count += 1
                        self.stdout.write(f'Updated: {answer.answer_text} (Value: {answer.answer_value})')
                        
                except RiskQuestion.DoesNotExist:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Question not found for ID: {row["QuestionID"]}')
                    )
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'Error processing answer {row["AnswerID"]}: {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Answers imported! Created: {created_count}, Updated: {updated_count}, Errors: {error_count}'
                )
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing answers: {str(e)}'))