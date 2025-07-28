from enum import Enum, auto

class Duration(Enum):
    OneQuarter = auto()
    TwoQuarters = auto()
    ThreeQuarters = auto()
    Year = auto()
    Other = auto()

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