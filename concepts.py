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

class Concept(Enum):
    SharesOutstanding = auto()
    Assets = auto()
    Equity = auto()
    Revenue = auto()
    NetIncome = auto()
    CashFlowFromOperatingActivities = auto()
    CashFlowFromInvestingActivities = auto()
    CashFlowFromFinancingActivities = auto()

class Alias():
    def __init__(self, weight: int, name: str, concept: Concept):
        self.weight: int = weight # determines relative priority vs other aliases for a given concept
        self.name: str = name
        self.concept: Concept = concept

strToAlias = {alias.name: alias for alias in [
    # SharesOutstanding (uses highest value, weight doesn't matter)
    Alias(0, 'EntityCommonStockSharesOutstanding', Concept.SharesOutstanding),
    Alias(0, 'CommonStockSharesOutstanding', Concept.SharesOutstanding),
    Alias(0, 'WeightedAverageNumberOfDilutedSharesOutstanding', Concept.SharesOutstanding),
    Alias(0, 'WeightedAverageNumberOfSharesOutstandingBasic', Concept.SharesOutstanding),
    # Assets
    Alias(0, 'Assets', Concept.Assets),
    # Equity
    Alias(2, 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest', Concept.Equity),
    Alias(2, 'PartnersCapitalIncludingPortionAttributableToNoncontrollingInterest', Concept.Equity),
    Alias(0, 'StockholdersEquity', Concept.Equity),
    Alias(0, 'PartnersCapital', Concept.Equity),
    # Revenue
    Alias(16, 'RevenueFromContractWithCustomerExcludingAssessedTax', Concept.Revenue),
    Alias(14, 'RevenueFromContractWithCustomerIncludingAssessedTax', Concept.Revenue),
    Alias(12, 'RegulatedAndUnregulatedOperatingRevenue', Concept.Revenue),
    Alias(10, 'RevenuesNetOfInterestExpense', Concept.Revenue),
    Alias(8, 'SalesRevenueServicesNet', Concept.Revenue),
    Alias(6, 'SalesRevenueGoodsNet', Concept.Revenue),
    Alias(4, 'NoninterestIncome', Concept.Revenue),
    Alias(2, 'SalesRevenueNet', Concept.Revenue),
    Alias(0, 'Revenues', Concept.Revenue),
    # Net Income
    Alias(8, 'NetIncomeLossAvailableToCommonStockholdersBasic', Concept.NetIncome),
    Alias(6, 'IncomeLossFromContinuingOperations', Concept.NetIncome),
    Alias(4, 'NetIncomeLoss', Concept.NetIncome),
    Alias(2, 'ProfitLoss', Concept.NetIncome),
    # Cash Flow from Operating Activities
    Alias(2, 'NetCashProvidedByUsedInOperatingActivities', Concept.CashFlowFromOperatingActivities),
    Alias(0, 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations', Concept.CashFlowFromOperatingActivities),
    # Cash Flow from Investing Activities
    Alias(2, 'NetCashProvidedByUsedInInvestingActivities', Concept.CashFlowFromInvestingActivities),
    Alias(0, 'NetCashProvidedByUsedInInvestingActivitiesContinuingOperations', Concept.CashFlowFromInvestingActivities),
    # Cash Flow from Financing Activities
    Alias(2, 'NetCashProvidedByUsedInFinancingActivities', Concept.CashFlowFromFinancingActivities),
    Alias(0, 'NetCashProvidedByUsedInFinancingActivitiesContinuingOperations', Concept.CashFlowFromFinancingActivities),
]}