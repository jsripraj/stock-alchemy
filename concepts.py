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
    Q4 = 4

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
    'SalesRevenueGoodsNet': Concepts.Revenue,
    'NetIncomeLoss' : Concepts.NetIncome,
    'ProfitLoss' : Concepts.NetIncome,
    'IncomeLossFromContinuingOperations' : Concepts.NetIncome,
    'NetIncomeLossAvailableToCommonStockholdersBasic' : Concepts.NetIncome,
    'NetCashProvidedByUsedInOperatingActivities' : Concepts.CashFlowFromOperatingActivities,
    'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations': Concepts.CashFlowFromOperatingActivities,
    'NetCashProvidedByUsedInInvestingActivities' : Concepts.CashFlowFromInvestingActivities,
    'NetCashProvidedByUsedInInvestingActivitiesContinuingOperations': Concepts.CashFlowFromInvestingActivities,
    'NetCashProvidedByUsedInFinancingActivities' : Concepts.CashFlowFromFinancingActivities,
    'NetCashProvidedByUsedInFinancingActivitiesContinuingOperations': Concepts.CashFlowFromFinancingActivities,
}