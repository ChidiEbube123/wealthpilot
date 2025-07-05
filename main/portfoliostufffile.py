import yfinance as yf
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt import plotting 
import pandas as pd
import matplotlib.pyplot as plt
class Allocation:
  def __init__(self, ticker, percentage):
    self.ticker = ticker
    self.percentage = percentage
    self.units = 0.0

class Portfolio:

  def __init__(self, tickerString: str, expectedReturn: float, portfolioName: str, riskBucket: int):

    self.name = portfolioName
    self.riskBucket = riskBucket
    self.expectedReturn = expectedReturn
    self.allocations = []

    from pypfopt.efficient_frontier import EfficientFrontier
    from pypfopt import risk_models
    from pypfopt import expected_returns

    df = self.__getDailyPrices(tickerString, "20y")

    mu = expected_returns.mean_historical_return(df)
    S = risk_models.sample_cov(df)

    ef = EfficientFrontier(mu, S)

    ef.efficient_return(expectedReturn)
    self.expectedRisk = ef.portfolio_performance()[1]
    portfolioWeights = ef.clean_weights()

    for key, value in portfolioWeights.items():
      newAllocation = Allocation(key, value)
      self.allocations.append(newAllocation)

  def __getDailyPrices(self, tickerStringList, period):
    data = yf.download(tickerStringList, group_by="Ticker", period=period)
    data = data.iloc[:, data.columns.get_level_values(1)=="Close"]
    data = data.dropna()
    data.columns = data.columns.droplevel(1)
    return data

  def printPortfolio(self):
    print("Portfolio Name: " + self.name)
    print("Risk Bucket: " + str(self.riskBucket))
    print("Expected Return: " + str(self.expectedReturn))
    print("Expected Risk: " + str(self.expectedRisk))
    print("Allocations: ")
    for allocation in self.allocations:
      print("Ticker: " + allocation.ticker + ", Percentage: " + str(allocation.percentage))

  @staticmethod
  def getPortfolioMapping(riskToleranceScore, riskCapacityScore):
    allocationLookupTable=pd.read_csv('./RiskMappingLookup.csv')
    matchTol = (allocationLookupTable['Tolerance_min'] <= riskToleranceScore) & (allocationLookupTable['Tolerance_max'] >= riskToleranceScore)
    matchCap = (allocationLookupTable['Capacity_min'] <= riskCapacityScore) & (allocationLookupTable['Capacity_max'] >= riskCapacityScore)
    portfolioID = allocationLookupTable['Portfolio'][(matchTol & matchCap)]
    return portfolioID.values[0]

class Goal:
  def __init__(self, name: str, targetYear: int, targetValue: float, portfolio: Portfolio=None, initialContribution: float=0, monthlyContribution: float=0, priority: str=""):
    self.name = name
    self.targetYear = targetYear
    self.targetValue = targetValue
    self.initialContribution = initialContribution
    self.monthlyContribution = monthlyContribution
    if not (priority == "") and not (priority in ["Dreams", "Wishes", "Wants", "Needs"]):
            raise ValueError("Wrong value set for Priority.")
    self.priority = priority
    self.portfolio = portfolio

  def getGoalProbabilities(self):
    if (self.priority == ""):
            raise ValueError("No value set for Priority.")
    lookupTable=pd.read_csv("./Data/Goal Probability Table.csv")
    match = (lookupTable["Realize"] == self.priority)
    minProb = lookupTable["MinP"][(match)]
    maxProb = lookupTable["MaxP"][(match)]
    return minProb.values[0], maxProb.values[0]

class AccountType():
  def __init__(self, value: str):
    if not value in("Taxable", "Roth IRA", "Traditional IRA"):
      raise ValueError("Allowed types: Taxable, Roth IRA, Traditional IRA")
    self.value = value
  def __eq__(self, other):
      return self.value == other.value

class AccountStatus():
  def __init__(self, value: str):
    if not value in("PENDING", "IN_REVIEW", "APPROVED", "REJECTED", "SUSPENDED"):
      raise ValueError("Allowed statuses: PENDING, IN_REVIEW, APPROVED, REJECTED, SUSPENDED")
    self.value = value
  def __eq__(self, other):
      return self.value == other.value

class Account():
  def __init__(self, number: str, accountType: AccountType, accountStatus: AccountStatus, cashBalance: float=0.0):
    self.goals = []
    self.number = number
    self.cashBalance = cashBalance
    self.accountType = accountType
    self.accountStatus = accountStatus

#myPortfolio = Portfolio("VTI TLT IEI GLD DBC", expectedReturn = 0.010, portfolioName = "Moderate", riskBucket = 3)
portfolio_id = Portfolio.getPortfolioMapping(2, 4)
print(portfolio_id)


# Create Our Own Mapping Nonesense
#Do for the nigerian market
# Create ortfolios for the nngxx

'''

Name	Symbol
VETIVA BANKING ETF	VETBANK
VETIVA CONSUMER GOODS ETF	VETGOODS
VETIVA INDUSTRIAL ETF	VETINDETF
VETIVA GRIFFIN 30 ETF	VETGRIF30
LOTUS HALAL EQUITY ETF	LOTUSHAL15
THE SIAML PENSION ETF 40	SIAMLETF40
GREENWICH ALPHA ETF	GREENWETF
MERISTEM VALUE EXCHANGE TRADED FUND	MERVALUE
VETIVA S & P NIGERIA SOVEREIGN BOND ETF	VSPBONDETF
MERISTEM GROWTH EXCHANGE TRADED FUND	MERGROWTH
NEWGOLD EXCHANGE TRADED FUND (ETF)	NEWGOLD
STANBIC IBTC ETF 30	STANBICETF30

'''