from enum import Enum, auto

class PeriodType(Enum):
    Quarter = auto()
    Year = auto()
    Other = auto()

class Concepts(Enum):
    Revenue = auto()
    NetIncome = auto()

aliasToConcept = {
    'RevenueFromContractWithCustomerExcludingAssessedTax': Concepts.Revenue,
    'Revenues': Concepts.Revenue,
    'SalesRevenueNet': Concepts.Revenue,
    'NetIncomeLoss' : Concepts.NetIncome,
}