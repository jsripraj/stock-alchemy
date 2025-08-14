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
    CashAndCashEquivalents = auto()
    Assets = auto()
    ShortTermDebt = auto()
    LongTermDebt = auto()
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
    # Shares Outstanding (uses highest value, weight doesn't matter)
    Alias(0, 'EntityCommonStockSharesOutstanding', Concept.SharesOutstanding),
    Alias(0, 'CommonStockSharesOutstanding', Concept.SharesOutstanding),
    Alias(0, 'WeightedAverageNumberOfDilutedSharesOutstanding', Concept.SharesOutstanding),
    Alias(0, 'WeightedAverageNumberOfSharesOutstandingBasic', Concept.SharesOutstanding),
    # Cash and Equivalents
    Alias(6, 'CashAndCashEquivalentsAtCarryingValue', Concept.CashAndCashEquivalents),
    Alias(4, 'CashCashEquivalentsAndShortTermInvestments', Concept.CashAndCashEquivalents),
    Alias(3, 'CashAndCashEquivalentsAtCarryingValueIncludingDiscontinuedOperations', Concept.CashAndCashEquivalents),
    Alias(2, 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', Concept.CashAndCashEquivalents),
    Alias(0, 'CashCashEquivalentsAndFederalFundsSold', Concept.CashAndCashEquivalents),
    Alias(0, 'CashAndDueFromBanks', Concept.CashAndCashEquivalents),
    Alias(0, 'Cash', Concept.CashAndCashEquivalents),
    # Assets
    Alias(0, 'Assets', Concept.Assets),
    # Short-Term Debt
    Alias(4, 'DebtCurrent', Concept.ShortTermDebt),
    Alias(4, 'LongTermDebtCurrent', Concept.ShortTermDebt),
    Alias(4, 'LongTermDebtAndCapitalLeaseObligationsCurrent', Concept.ShortTermDebt),
    Alias(4, 'ShortTermBorrowings', Concept.ShortTermDebt),
    Alias(4, 'NotesPayableCurrent', Concept.ShortTermDebt),
    Alias(2, 'ConvertibleNotesPayableCurrent', Concept.ShortTermDebt),
    Alias(2, 'OtherShortTermBorrowings', Concept.ShortTermDebt),
    Alias(2, 'CommercialPaper', Concept.ShortTermDebt),
    Alias(0, 'ConvertibleDebtCurrent', Concept.ShortTermDebt),
    # Long-Term Debt
    Alias(2, 'LongTermDebtAndCapitalLeaseObligations', Concept.LongTermDebt),
    Alias(2, 'LongTermDebtNoncurrent', Concept.LongTermDebt),
    Alias(2, 'LongTermDebt', Concept.LongTermDebt),
    Alias(2, 'LongTermNotesAndLoans', Concept.LongTermDebt),
    Alias(2, 'LongTermNotesPayable', Concept.LongTermDebt),
    Alias(1, 'SeniorLongTermNotes', Concept.LongTermDebt),
    Alias(0, 'ConvertibleLongTermNotesPayable', Concept.LongTermDebt),
    Alias(-1, 'LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities', Concept.LongTermDebt),
    Alias(-2, 'DebtInstrumentCarryingAmount', Concept.LongTermDebt),
    Alias(-4, 'DebtLongtermAndShorttermCombinedAmount', Concept.LongTermDebt),
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

excuses = {
    '0000002488', # Doesn’t have/report ST-debt
    '0000006951', # Applied Materials doesn’t have/report st debt
    '0000018230', # Caterpillar: don't report quarterly ST- or LT-debt
    '0000034088', # Exxon doesn’t report Revenues for 2015-03-31, 2015-06-30, 2015-09-30 and same for 2016
    '0000040545', # No quarterly cash from 2015-03-31 to 2016-09-30
    '0000063908', # McDonald's: no quarterly ST-debt
    '0000064040', # S&P Global doesn’t report a lot for 2024-12-31, no ST debt through 2021-09-30
    '0000080661', # Progressive doesn't report ST debt (they combine with LT debt)
    '0000109198', # TJX doesn't break out ST debt
    '0000315189', # Deere: can't find LT debt alias starting 2022-07-31 and ST debt alias thru 2020-05-03
    '0000316709', # Schwab: doesn't report ST debt
    '0000796343', # Adobe: Doesn’t have/report ST-debt
    '0000895421', # Morgan Stanley: Doesn't break out ST-debt
    '0000896878', # ST debt
    '0001035267', # Intuitive Surgical: No debt
    '0001067983', # Berkshire Hathaway doesn’t really report EntityCommonStockSharesOutstanding, can't find debt either
    '0001075531', # Doesn’t have/report ST-debt
    '0001108524', # Salesforce: Doesn't have ST debt
    '0001283699', # T-Mobile: Can't find LT debt alias
    '0001321655', # Palantir: no debt
    '0001321655', # Meta: no debt
    '0001341439', # Oracle: 2016-02-29 no ST debt
    '0001403161', # Visa doesn’t report shares outstanding
    '0001707925', # Linde doesn’t report any cash flow in 2018 before 2018-09-30
}