from enum import Enum, auto

class Duration(Enum):
    Other = 0
    OneQuarter = 1
    TwoQuarters = 2
    ThreeQuarters = 3
    Year = 4

class FiscalPeriod(Enum):
    Q1 = 1
    Q2 = 2
    Q3 = 3
    FY = 4

class Concepts(Enum):
    Revenue = auto()
    NetIncome = auto()
    CashFlowFromOperatingActivities = auto()
    CashFlowFromInvestingActivities = auto()
    CashFlowFromFinancingActivities = auto()

aliasToConcept = {
    'RevenueFromContractWithCustomerExcludingAssessedTax': Concepts.Revenue,
    'Revenues': Concepts.Revenue,
    'SalesRevenueNet': Concepts.Revenue,
    'NoninterestIncome': Concepts.Revenue,
    'NetIncomeLoss' : Concepts.NetIncome,
    'NetCashProvidedByUsedInOperatingActivities' : Concepts.CashFlowFromOperatingActivities,
    'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations': Concepts.CashFlowFromOperatingActivities,
    'NetCashProvidedByUsedInInvestingActivities' : Concepts.CashFlowFromInvestingActivities,
    'NetCashProvidedByUsedInInvestingActivitiesContinuingOperations': Concepts.CashFlowFromInvestingActivities,
    'NetCashProvidedByUsedInFinancingActivities' : Concepts.CashFlowFromFinancingActivities,
    'NetCashProvidedByUsedInFinancingActivitiesContinuingOperations': Concepts.CashFlowFromFinancingActivities,
}