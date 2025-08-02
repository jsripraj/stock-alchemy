from enum import Enum, auto

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

class Concepts(Enum):
    Revenue = auto()
    NetIncome = auto()
    CashFlowFromOperatingActivities = auto()
    CashFlowFromInvestingActivities = auto()
    CashFlowFromFinancingActivities = auto()

aliasToConcept = {
    # Revenue
    'RevenueFromContractWithCustomerExcludingAssessedTax': Concepts.Revenue,
    'RevenueFromContractWithCustomerIncludingAssessedTax': Concepts.Revenue,
    'Revenues': Concepts.Revenue,
    'SalesRevenueNet': Concepts.Revenue,
    'NoninterestIncome': Concepts.Revenue,
    'SalesRevenueGoodsNet': Concepts.Revenue,
    'SalesRevenueServicesNet': Concepts.Revenue,
    'RevenuesNetOfInterestExpense': Concepts.Revenue,
    'RegulatedAndUnregulatedOperatingRevenue': Concepts.Revenue,
    # Net Income
    'NetIncomeLoss': Concepts.NetIncome,
    'ProfitLoss': Concepts.NetIncome,
    'IncomeLossFromContinuingOperations': Concepts.NetIncome,
    'NetIncomeLossAvailableToCommonStockholdersBasic': Concepts.NetIncome,
    # Cash Flow from Operating Activities
    'NetCashProvidedByUsedInOperatingActivities': Concepts.CashFlowFromOperatingActivities,
    'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations': Concepts.CashFlowFromOperatingActivities,
    # Cash Flow from Investing Activities
    'NetCashProvidedByUsedInInvestingActivities': Concepts.CashFlowFromInvestingActivities,
    'NetCashProvidedByUsedInInvestingActivitiesContinuingOperations': Concepts.CashFlowFromInvestingActivities,
    # Cash Flow from Financing Activities
    'NetCashProvidedByUsedInFinancingActivities': Concepts.CashFlowFromFinancingActivities,
    'NetCashProvidedByUsedInFinancingActivitiesContinuingOperations': Concepts.CashFlowFromFinancingActivities,
}