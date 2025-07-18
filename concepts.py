from enum import Enum, auto

class PeriodType(Enum):
    Quarter = auto()
    Year = auto()
    Other = auto()

class Concept(Enum):
    Revenue = auto()

aliasToConcept = {
    'RevenueFromContractWithCustomerExcludingAssessedTax': Concept.Revenue,
    'Revenues': Concept.Revenue,
    'SalesRevenueNet': Concept.Revenue
}