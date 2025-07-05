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
        df = self._get_prices("20y")
        mu = expected_returns.mean_historical_return(df)
        S = risk_models.sample_cov(df)
        ef = EfficientFrontier(mu, S)
        ef.efficient_return(self.expected_return)
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
        df = pd.read_csv('./RiskMappingLookup.csv')
        match_tol = (df['Tolerance_min'] <= tol_score) & (df['Tolerance_max'] >= tol_score)
        match_cap = (df['Capacity_min'] <= cap_score) & (df['Capacity_max'] >= cap_score)
        return df['Portfolio'][(match_tol & match_cap)].values[0]
