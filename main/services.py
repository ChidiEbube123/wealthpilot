import yfinance as yf
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import expected_returns, risk_models
import pandas as pd

class PortfolioService:
    def __init__(self, tickers: str, expected_return: float):
        self.tickers = tickers.split()
        self.expected_return = expected_return
        self.allocations = []
        self.expected_risk = 0.0

    def create(self):

            price_data = self._get_prices("20y")
            mu = expected_returns.mean_historical_return(price_data)
            S = risk_models.sample_cov(price_data)

            try:
                ef = EfficientFrontier(mu, S)
                ef.efficient_return(self.expected_return)
            except Exception as e:
                print(f"efficient_return failed. Falling back to max Sharpe. Reason: {e}")
                
                # Recreate ef object before fallback
                ef = EfficientFrontier(mu, S)
                ef.max_sharpe()

            self.expected_risk = ef.portfolio_performance()[1]
            weights = ef.clean_weights()
            self.allocations = [{"ticker": k, "percentage": v} for k, v in weights.items()]
            return self

                            
                 


    def _get_prices(self, period):
        data = yf.download(self.tickers, group_by="Ticker", period=period)
        data = data.iloc[:, data.columns.get_level_values(1) == "Close"]
        data = data.dropna()
        data.columns = data.columns.droplevel(1)
        return data

    @staticmethod
    def get_portfolio_id(tol_score, cap_score):
        df = pd.read_csv('main/RiskMappingLookuptampered.csv')
        match_tol = (df['Tolerance_min'] <= tol_score) & (df['Tolerance_max'] >= tol_score)
        match_cap = (df['Capacity_min'] <= cap_score) & (df['Capacity_max'] >= cap_score)
        match = df[match_tol & match_cap]
        if not match.empty:
            return match['Portfolio'].values[0]
        else:
            raise ValueError(f"No portfolio mapping found for Tolerance Score: {tol_score}, Capacity Score: {cap_score}")


'''
# services.py - Core business logic services

import numpy as np
import pandas as pd
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from typing import Dict, List, Tuple, Optional
from .models import *
import logging

logger = logging.getLogger(__name__)

class RiskProfileService:
    """Service for risk profiling and assessment"""
    
    @staticmethod
    def calculate_risk_score(questionnaire_answers: Dict) -> Tuple[int, int, int]:
        """
        Calculate risk tolerance, capacity, and overall score
        Returns: (risk_tolerance_score, risk_capacity_score, overall_score)
        """
        # Risk tolerance questions (1-10 scale)
        tolerance_questions = [
            'market_volatility_comfort',
            'loss_tolerance',
            'investment_experience',
            'time_horizon_comfort'
        ]
        
        # Risk capacity questions (1-10 scale)
        capacity_questions = [
            'income_stability',
            'emergency_fund_months',
            'debt_to_income_ratio',
            'investment_timeframe'
        ]
        
        tolerance_score = sum(questionnaire_answers.get(q, 5) for q in tolerance_questions) // len(tolerance_questions)
        capacity_score = sum(questionnaire_answers.get(q, 5) for q in capacity_questions) // len(capacity_questions)
        
        # Overall score combines both (1-100 scale)
        overall_score = int((tolerance_score * 0.6 + capacity_score * 0.4) * 10)
        
        return tolerance_score, capacity_score, overall_score
    
    @staticmethod
    def recommend_portfolio(risk_score: int) -> ModelPortfolio:
        """Recommend model portfolio based on risk score"""
        if risk_score <= 20:
            risk_level = 1
        elif risk_score <= 40:
            risk_level = 2
        elif risk_score <= 60:
            risk_level = 3
        elif risk_score <= 80:
            risk_level = 4
        else:
            risk_level = 5
        
        return ModelPortfolio.objects.filter(
            risk_level=risk_level, 
            is_active=True
        ).first()

class PortfolioService:
    """Service for portfolio management and Modern Portfolio Theory calculations"""
    
    @staticmethod
    def calculate_efficient_frontier(assets: List[Asset], 
                                   returns_data: pd.DataFrame,
                                   num_portfolios: int = 10000) -> Dict:
        """
        Calculate efficient frontier using Modern Portfolio Theory
        """
        returns = returns_data.pct_change().dropna()
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        num_assets = len(assets)
        results = np.zeros((3, num_portfolios))
        
        np.random.seed(42)
        
        for i in range(num_portfolios):
            # Random weights
            weights = np.random.random(num_assets)
            weights /= np.sum(weights)
            
            # Calculate portfolio return and volatility
            portfolio_return = np.sum(weights * mean_returns) * 252
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
            sharpe_ratio = portfolio_return / portfolio_volatility
            
            results[0, i] = portfolio_return
            results[1, i] = portfolio_volatility
            results[2, i] = sharpe_ratio
        
        return {
            'returns': results[0],
            'volatilities': results[1],
            'sharpe_ratios': results[2]
        }
    
    @staticmethod
    def calculate_goal_probability(goal: Goal, monte_carlo_runs: int = 10000) -> float:
        """
        Monte Carlo simulation for goal achievement probability
        """
        if not goal.model_portfolio:
            return 0.0
        
        portfolio = goal.model_portfolio
        years_to_goal = (goal.target_date - timezone.now().date()).days / 365.25
        
        # Convert to float for calculations
        expected_return = float(portfolio.expected_return)
        expected_risk = float(portfolio.expected_risk)
        initial_investment = float(goal.initial_investment)
        monthly_contribution = float(goal.monthly_contribution)
        target_amount = float(goal.target_amount)
        
        successful_runs = 0
        
        for _ in range(monte_carlo_runs):
            portfolio_value = initial_investment
            
            for month in range(int(years_to_goal * 12)):
                # Add monthly contribution
                portfolio_value += monthly_contribution
                
                # Generate random return
                monthly_return = np.random.normal(
                    expected_return / 12, 
                    expected_risk / np.sqrt(12)
                )
                
                # Apply return
                portfolio_value *= (1 + monthly_return)
            
            if portfolio_value >= target_amount:
                successful_runs += 1
        
        return successful_runs / monte_carlo_runs

class OrderService:
    """Service for order management and execution"""
    
    @staticmethod
    def validate_order(order_data: Dict) -> Tuple[bool, str]:
        """Validate order before submission"""
        account = Account.objects.get(id=order_data['account_id'])
        
        # Check account status
        if account.status != 'APPROVED':
            return False, "Account not approved for trading"
        
        # Check market hours (simplified)
        now = timezone.now()
        if now.hour < 9 or now.hour > 16:  # NYSE hours
            return False, "Market is closed"
        
        # Check cash balance for buy orders
        if order_data['order_type'] == 'BUY':
            if account.cash_balance < Decimal(str(order_data['dollar_amount'])):
                return False, "Insufficient cash balance"
        
        return True, "Order validated"
    
    @staticmethod
    def split_goal_order(goal: Goal, dollar_amount: Decimal) -> List[Dict]:
        """Split a goal-level order into individual asset orders"""
        if not goal.model_portfolio:
            return []
        
        orders = []
        allocations = PortfolioAllocation.objects.filter(
            portfolio=goal.model_portfolio
        )
        
        for allocation in allocations:
            order_amount = dollar_amount * (allocation.allocation_percentage / 100)
            orders.append({
                'asset': allocation.asset,
                'dollar_amount': order_amount,
                'allocation_percentage': allocation.allocation_percentage
            })
        
        return orders
    
    @staticmethod
    def aggregate_orders(orders: List[Order]) -> Dict[Asset, Decimal]:
        """Aggregate individual orders into master orders"""
        aggregated = {}
        
        for order in orders:
            if order.asset not in aggregated:
                aggregated[order.asset] = Decimal('0')
            
            if order.order_type == 'BUY':
                aggregated[order.asset] += order.dollar_amount
            else:  # SELL
                aggregated[order.asset] -= order.dollar_amount
        
        return aggregated
    
    @staticmethod
    def allocate_filled_orders(master_fills: Dict, original_orders: List[Order]):
        """Allocate filled master orders back to individual accounts"""
        for order in original_orders:
            if order.asset in master_fills:
                fill_data = master_fills[order.asset]
                
                # Calculate allocation based on order size
                total_order_amount = sum(
                    o.dollar_amount for o in original_orders 
                    if o.asset == order.asset
                )
                
                allocation_ratio = order.dollar_amount / total_order_amount
                filled_shares = fill_data['shares'] * allocation_ratio
                
                # Update order
                order.shares = filled_shares
                order.price_per_share = fill_data['price']
                order.status = 'FILLED'
                order.filled_at = timezone.now()
                order.save()
                
                # Update holdings
                OrderService._update_holdings(order, filled_shares)
    
    @staticmethod
    def _update_holdings(order: Order, shares: Decimal):
        """Update holdings after order execution"""
        holding, created = Holding.objects.get_or_create(
            account=order.account,
            goal=order.goal,
            asset=order.asset,
            defaults={'shares': Decimal('0'), 'average_cost': Decimal('0')}
        )
        
        if order.order_type == 'BUY':
            # Update average cost
            total_cost = (holding.shares * holding.average_cost + 
                         shares * order.price_per_share)
            holding.shares += shares
            holding.average_cost = total_cost / holding.shares if holding.shares > 0 else Decimal('0')
        else:  # SELL
            holding.shares -= shares
            if holding.shares <= 0:
                holding.shares = Decimal('0')
                holding.average_cost = Decimal('0')
        
        holding.save()

class RebalanceService:
    """Service for portfolio rebalancing"""
    
    @staticmethod
    def calculate_portfolio_drift(goal: Goal) -> Dict[Asset, Decimal]:
        """Calculate how much the portfolio has drifted from target allocation"""
        if not goal.model_portfolio:
            return {}
        
        target_allocations = {
            pa.asset: pa.allocation_percentage
            for pa in PortfolioAllocation.objects.filter(portfolio=goal.model_portfolio)
        }
        
        # Get current holdings
        holdings = Holding.objects.filter(goal=goal)
        
        # Calculate current market values
        total_value = Decimal('0')
        current_values = {}
        
        for holding in holdings:
            market_value = holding.market_value
            current_values[holding.asset] = market_value
            total_value += market_value
        
        # Calculate drift
        drift = {}
        for asset, target_pct in target_allocations.items():
            current_value = current_values.get(asset, Decimal('0'))
            current_pct = (current_value / total_value * 100) if total_value > 0 else Decimal('0')
            drift[asset] = current_pct - target_pct
        
        return drift
    
    @staticmethod
    def should_rebalance(goal: Goal, threshold: Decimal = Decimal('5.0')) -> bool:
        """Check if rebalancing is needed based on drift threshold"""
        drift = RebalanceService.calculate_portfolio_drift(goal)
        return any(abs(d) > threshold for d in drift.values())
    
    @staticmethod
    def generate_rebalance_orders(goal: Goal) -> List[Dict]:
        """Generate orders needed to rebalance portfolio"""
        drift = RebalanceService.calculate_portfolio_drift(goal)
        
        # Calculate total portfolio value
        total_value = sum(
            holding.market_value 
            for holding in Holding.objects.filter(goal=goal)
        )
        
        rebalance_orders = []
        
        for asset, drift_pct in drift.items():
            if abs(drift_pct) > Decimal('1.0'):  # Only rebalance if drift > 1%
                order_amount = total_value * (drift_pct / 100)
                
                if order_amount > 0:
                    order_type = 'SELL'
                else:
                    order_type = 'BUY'
                    order_amount = abs(order_amount)
                
                rebalance_orders.append({
                    'asset': asset,
                    'order_type': order_type,
                    'dollar_amount': order_amount
                })
        
        return rebalance_orders

class PerformanceService:
    """Service for performance calculation and reporting"""
    
    @staticmethod
    def calculate_twrr(account: Account, goal: Goal, start_date: datetime, end_date: datetime) -> Decimal:
        """Calculate Time-Weighted Rate of Return"""
        transactions = Transaction.objects.filter(
            account=account,
            goal=goal,
            transaction_date__range=[start_date, end_date]
        ).order_by('transaction_date')
        
        if not transactions:
            return Decimal('0')
        
        # Get portfolio values at transaction dates
        portfolio_values = []
        cash_flows = []
        
        for transaction in transactions:
            # This is simplified - in practice you'd need market values at each date
            if transaction.transaction_type in ['DEPOSIT', 'WITHDRAWAL']:
                cash_flows.append(float(transaction.amount))
            
        # Simplified TWRR calculation - in practice this would be more complex
        # involving geometric mean of sub-period returns
        return Decimal('0.075')  # Placeholder
    
    @staticmethod
    def calculate_unrealized_gains(holding: Holding, current_price: Decimal) -> Decimal:
        """Calculate unrealized gains for a holding"""
        market_value = holding.shares * current_price
        cost_basis = holding.shares * holding.average_cost
        return market_value - cost_basis

class FeeService:
    """Service for fee calculation and management"""
    
    @staticmethod
    def calculate_management_fee(account: Account, aum_fee_rate: Decimal = Decimal('0.0075')) -> Decimal:
        """Calculate annual management fee based on AUM"""
        total_value = sum(
            holding.market_value 
            for holding in Holding.objects.filter(account=account)
        )
        
        return total_value * aum_fee_rate
    
    @staticmethod
    def charge_quarterly_fees(account: Account):
        """Charge quarterly management fees"""
        annual_fee = FeeService.calculate_management_fee(account)
        quarterly_fee = annual_fee / 4
        
        if quarterly_fee > 0:
            Fee.objects.create(
                account=account,
                fee_type='MANAGEMENT',
                amount=quarterly_fee,
                fee_rate=Decimal('0.0075'),
                calculation_date=timezone.now().date(),
                charged_date=timezone.now().date(),
                description='Quarterly management fee'
            )
            
            # Deduct fee from cash balance
            account.cash_balance -= quarterly_fee
            account.save()

class MarketDataService:
    """Service for market data management"""
    
    @staticmethod
    def update_holdings_market_value():
        """Update market values for all holdings"""
        holdings = Holding.objects.all()
        
        for holding in holdings:
            latest_market_data = MarketData.objects.filter(
                asset=holding.asset
            ).order_by('-date').first()
            
            if latest_market_data:
                holding.market_value = holding.shares * latest_market_data.close_price
                holding.save()
    
    @staticmethod
    def fetch_market_data(asset: Asset, date: datetime) -> Optional[MarketData]:
        """Fetch market data for specific asset and date"""
        try:
            return MarketData.objects.get(asset=asset, date=date.date())
        except MarketData.DoesNotExist:
            return None
'''