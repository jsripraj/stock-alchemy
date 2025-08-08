from enum import Enum, auto
from datetime import datetime

class Duration(Enum):
    Other = 0
    OneQuarter = 1
    TwoQuarters = 2
    ThreeQuarters = 3
    Year = 4

class Period(Enum):
    Q1 = 1
    Q2 = 2
    Q3 = 3
    Q4 = 4
    FY = 4

class Concept(Enum):
    Revenue = auto()
    NetIncome = auto()
    CashFlowFromOperatingActivities = auto()
    CashFlowFromInvestingActivities = auto()
    CashFlowFromFinancingActivities = auto()

aliasToConcept = {
    # Revenue
    'RevenueFromContractWithCustomerExcludingAssessedTax': Concept.Revenue,
    'RevenueFromContractWithCustomerIncludingAssessedTax': Concept.Revenue,
    'Revenues': Concept.Revenue,
    'SalesRevenueNet': Concept.Revenue,
    'NoninterestIncome': Concept.Revenue,
    'SalesRevenueGoodsNet': Concept.Revenue,
    'SalesRevenueServicesNet': Concept.Revenue,
    'RevenuesNetOfInterestExpense': Concept.Revenue,
    'RegulatedAndUnregulatedOperatingRevenue': Concept.Revenue,
    # Net Income
    'NetIncomeLoss': Concept.NetIncome,
    'ProfitLoss': Concept.NetIncome,
    'IncomeLossFromContinuingOperations': Concept.NetIncome,
    'NetIncomeLossAvailableToCommonStockholdersBasic': Concept.NetIncome,
    # Cash Flow from Operating Activities
    'NetCashProvidedByUsedInOperatingActivities': Concept.CashFlowFromOperatingActivities,
    'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations': Concept.CashFlowFromOperatingActivities,
    # Cash Flow from Investing Activities
    'NetCashProvidedByUsedInInvestingActivities': Concept.CashFlowFromInvestingActivities,
    'NetCashProvidedByUsedInInvestingActivitiesContinuingOperations': Concept.CashFlowFromInvestingActivities,
    # Cash Flow from Financing Activities
    'NetCashProvidedByUsedInFinancingActivities': Concept.CashFlowFromFinancingActivities,
    'NetCashProvidedByUsedInFinancingActivitiesContinuingOperations': Concept.CashFlowFromFinancingActivities,
}