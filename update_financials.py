import requests
import os
import zipfile
import json
import pprint
import mysql.connector
from collections import defaultdict
import datetime
import config
import concepts
from enum import Enum
import logging
import time

class FiscalValue:
    def __init__(self, concept: str, alias: str, value: str, fiscalYearOfFiling: str = None):
        self.concept = concept
        self.alias = alias
        self.value = value
        self.fiscalYearOfFiling = fiscalYearOfFiling

    def __repr__(self):
        return f"FiscalValue('{self.concept}', '{self.alias}', '{self.value}', '{self.fiscalYearOfFiling}')"

class FiscalFinancial:
    def __init__(self, cik: str, fId: str, duration: Enum, end: str, accn: str, form: str, fy: str , fp: Enum):
        self.cik: str = cik
        self.fId: str = fId # fiscal ID
        self.duration: Enum = duration
        self.end: str = end
        self.accn: str = accn # Accession number
        self.form: str = form
        self.fy: str = fy # Fiscal year
        self.fp: Enum = fp # Fiscal period (indicates end of period, does NOT indicate duration)
        self.values: dict[str, list[FiscalValue]] = defaultdict(list) # concept to values

    def __repr__(self):
        return f"FiscalFinancial(cik: {self.cik}, fId: {self.fId}, duration: {self.duration.name}, " + \
               f"end: {self.end}, accn: {self.accn}, form: {self.form}, " + \
               f"fy: {self.fy}, fp: {self.fp.name}, values: {pprint.pformat(self.values)}"
    
def strToDate(dateStr: str) -> datetime:
    return datetime.datetime.strptime(dateStr, "%Y-%m-%d")

def dateToStr(date: datetime.datetime) -> str:
    return date.strftime("%Y-%m-%d")

def createFId(cik: str, fy: int, fp: Enum, duration: Enum) -> str:
    '''
    Returns a Fiscal ID: cik, fy, fp, and Duration, connected by underscores.

    For example: 0000034088_2023_Q3_OneQuarter
    '''
    try:
        return "_".join([cik, str(fy), fp.name, duration.name])
    except TypeError as e:
        log(logging.debug, cik, f'createFId: {e}')
        return None

# def deconstructFId(fId: str) -> tuple[str, str, str, str]:
#     '''
#     Returns cik, fy, fp, Duration
#     '''
#     return fId.split('_')

def createFIdToFiscalFinancial(data: dict, cik: str) -> dict[str, dict] | None:
    '''
    Returns a dictionary mapping Fiscal ID to a FiscalFinancial with empty values, or None if the 
    dictionary cannot be created.

    In addition to the company-reported entries for FY with full year duration, Q3 with three 
    quarter duration, Q2 with two quarter duration, and Q1 with one quarter duration, this function 
    also creates one-quarter duration entries for Q4, Q3, and Q2. 
    '''
    if 'facts' not in data:
        log(logging.debug, cik, f'"facts" not found in JSON')
        return None
    if 'us-gaap' not in data['facts']:
        log(logging.debug, cik, f'"us-gaap" not found in JSON')
        return None
    if 'Assets' not in data['facts']['us-gaap']:
        log(logging.debug, cik, f'"Assets" not found in JSON')
        return None
    if 'units' not in data['facts']['us-gaap']['Assets']:
        log(logging.debug, cik, f'"units" not found in JSON')
        return None
    if 'USD' not in data['facts']['us-gaap']['Assets']['units']:
        log(logging.debug, cik, f'"USD" not found in JSON')
        return None

    accnToEntry = {}
    for entry in data['facts']['us-gaap']['Assets']['units']['USD']:
        if isDesiredForm(entry['form']):
            accn = entry['accn']
            # Use the most recent entry for each accn
            if (accn not in accnToEntry) or (entry['end'] > accnToEntry[accn]['end']):
                accnToEntry[accn] = entry

    fIdToFiscalFinancial = {}
    for entry in accnToEntry.values():
        end = entry['end']
        form = entry['form']
        accn = entry['accn']
        fiscalYear = entry['fy']
        fiscalPeriod = concepts.FiscalPeriod[entry['fp']]
        duration = getMaxDurationFromFiscalPeriod(fiscalPeriod)
        fId = createFId(cik, fiscalYear, fiscalPeriod, duration)
        fIdToFiscalFinancial[fId] = FiscalFinancial(cik, fId, duration, end, accn, form, fiscalYear, fiscalPeriod)

        # for FY, Q3, Q2, create another entry with a OneQuarter duration
        if duration.value > concepts.Duration.OneQuarter.value:
            newDuration = concepts.Duration.OneQuarter
            newFId = createFId(cik, fiscalYear, fiscalPeriod, newDuration)
            fIdToFiscalFinancial[newFId] = FiscalFinancial(cik, newFId, newDuration, end, None, None, fiscalYear, fiscalPeriod)
        else:
            pass
    return fIdToFiscalFinancial

def getConcepts(cik: str, data: dict, fIdToFiscalFinancial: dict, logger: logging.Logger) -> None:
    gaapData = data['facts']['us-gaap']
    for alias in gaapData.keys():
        if alias in concepts.aliasToConcept:
            entries = gaapData[alias]['units']['USD']
            for entry in entries:
                if not isDesiredForm(entry['form']):
                    continue
                end = entry['end']
                fy = entry['fy']
                fp = concepts.FiscalPeriod[entry['fp']]
                start = entry['start'] if 'start' in entry else None
                duration = getDurationFromDates(start, end)
                entryId = createFId(cik, fy, fp, duration)
                if entryId in fIdToFiscalFinancial:
                    concept = concepts.aliasToConcept[alias].name
                    value = entry['val']
                    existingValues = fIdToFiscalFinancial[entryId].values[concept]
                    fiscalYearOfFiling = entry['fy']
                    newValue = FiscalValue(concept, alias, value, fiscalYearOfFiling)
                    addFiscalValue(existingValues, newValue)
    addMissingOneQuarterConcepts(fIdToFiscalFinancial, logger)

def isDesiredForm(form: str) -> bool:
    return form == '10-K' or form == '10-Q'

def addFiscalValue(existingValues: list[FiscalValue], newValue: FiscalValue) -> None:
    '''
    Determines whether and how a FiscalValue should be added to a list, then adds it if necessary.
    '''
    # If the list is empty, append it
    if not existingValues:
        existingValues.append(newValue)
        return

    # If the new value is the same as an existing one, do nothing
    for i in range(len(existingValues)):
        if existingValues[i].value == newValue.value:
            return

    # If the new value is "better" than an existing value, replace the existing
    for i in range(len(existingValues)):
        if replaceFiscalValue(existingValues[i], newValue):
            existingValues[i] = newValue

    return

def replaceFiscalValue(A: FiscalValue, B: FiscalValue) -> bool:
    '''
    Returns True if FiscalValue A should be replaced by B. 
    
    A should be replaced by B if B is more recent (or at least not None).
    '''
    if B.fiscalYearOfFiling and (not A.fiscalYearOfFiling or B.fiscalYearOfFiling > A.fiscalYearOfFiling):
        return True

    return False


def addMissingOneQuarterConcepts(fIdToFiscalFinancial: dict, logger: logging.Logger) -> None:
    '''
    Add missing one-quarter-duration concepts. 

    For example, fourth quarter concepts could be missing if they are not reported and must 
    be derived. Also, cash flow concepts could be missing for Q2 and Q3 since they might be 
    reported only in two- and three-quarter durations. 
    '''
    for fId, ff in fIdToFiscalFinancial.items():
        if ff.duration == concepts.Duration.OneQuarter and ff.fp != concepts.FiscalPeriod.Q1:
            for concept in concepts.Concepts:
                concept = concept.name
                values = ff.values[concept]
                if not values:
                    value = getOneQuarterValue(fIdToFiscalFinancial, ff, concept, logger)
                    if value != None:
                        values.append(value)

def getOneQuarterValue(fIdToFf: dict[str, FiscalFinancial], ff: FiscalFinancial, concept: str, logger: logging.Logger) -> FiscalValue | None:
    longId, shortId = getLongShortOneQuarterFIds(ff, logger)
    if longId in fIdToFf and concept in fIdToFf[longId].values:
        longValues = fIdToFf[longId].values[concept]
        if len(longValues) == 1:
            if shortId in fIdToFf and concept in fIdToFf[shortId].values:
                shortValues = fIdToFf[shortId].values[concept]
                if len(shortValues) == 1:
                    longValue = longValues[0]
                    shortValue = shortValues[0]
                    resConcept = longValue.concept
                    resAlias = longValue.alias
                    resValue = str(int(longValue.value) - int(shortValue.value))
                    return FiscalValue(resConcept, resAlias, resValue)
    return None

def getLongShortOneQuarterFIds(ff: FiscalFinancial, logger: logging.Logger) -> tuple[str | None, str | None]:
    '''
    Returns long-duration fId and short-duration fId.

    For example, if the given FiscalFinancial is for Q3, the long-duration will fId have Q3 and 
    ThreeQuarter duration. The short-duration fId will have Q2 and TwoQuarter duration. 
    This function should only be used on one-quarter duration FiscalFinancials.
    '''
    if ff.duration != concepts.Duration.OneQuarter:
        msg = f'Cannot get long/short-duration FId of {ff.fp.name} fiscal period, FF: {ff}'
        log(logger.warning, ff.cik, msg)
        return None, None
    longDuration = getMaxDurationFromFiscalPeriod(ff.fp)
    longId = createFId(ff.cik, ff.fy, ff.fp, longDuration)
    shortFp = concepts.FiscalPeriod(ff.fp.value - 1)
    shortDuration = getMaxDurationFromFiscalPeriod(shortFp)
    shortId = createFId(ff.cik, ff.fy, shortFp, shortDuration)
    return longId, shortId

def handleConceptIssues(cik: str, fIdToFiscalFinancial: dict, logger) -> None:
        problemCount = 0
        for fId, ff in fIdToFiscalFinancial.items():
            values = ff.values
            for c in concepts.Concepts:
                concept = c.name
                data = values[concept]
                if len(data) != 1:
                    issue = f"No values found" if not data else f"{len(data)} values found => {data}"
                    msg = f"{ff.end} {ff.fp.name} {ff.duration.name} {concept}: {issue}"
                    log(logger.debug, cik, msg)
                    problemCount += 1
        if problemCount > 0:
            msg = f'{problemCount} problematic values'
            log(logger.debug, cik, msg)
            jsonFilename = f'CIK{cik}.json'
            extractZipFileToJson(jsonFilename)
        
def getMaxDurationFromFiscalPeriod(fp: Enum) -> Enum:
    if fp == concepts.FiscalPeriod.FY or fp == concepts.FiscalPeriod.Q4:
        return concepts.Duration.Year
    if fp == concepts.FiscalPeriod.Q3:
        return concepts.Duration.ThreeQuarters
    if fp == concepts.FiscalPeriod.Q2:
        return concepts.Duration.TwoQuarters
    if fp == concepts.FiscalPeriod.Q1:
        return concepts.Duration.OneQuarter
    return concepts.Duration.Other

def getDurationFromDates(startDate: str | None, endDate: str) -> Enum:
    if not startDate:
        return concepts.Duration.OneQuarter
    start = strToDate(startDate)
    end = strToDate(endDate)
    duration = (end - start).days
    if 70 < duration < 110:
        return concepts.Duration.OneQuarter
    if 160 < duration < 200:
        return concepts.Duration.TwoQuarters
    if 250 < duration < 290:
        return concepts.Duration.ThreeQuarters
    if 320 < duration < 390:
        return concepts.Duration.Year
    return concepts.Duration.Other

def extractZipFileToJson(filename: str):
    # filename = "CIK0000320193.json" # Apple
    with zipfile.ZipFile(config.ZIP_PATH, 'r') as zf:
        with zf.open(filename) as inFile:
            content = inFile.read()
            data = json.loads(content.decode('utf-8'))
            with open(os.path.join(config.LOG_DIR, filename), 'w') as outFile:
                json.dump(data, outFile, indent=2)

def configureLogger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logFile = os.path.join(config.LOG_DIR, f'update_financials.log')
    logging.basicConfig(filename=logFile, 
                        format='%(asctime)s %(levelname)s: %(message)s', 
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG,
                        filemode="w")
    return logger

def log(fn, cik: str, msg: str):
    fn(f'CIK {cik}: {msg}')

# Download companyfacts.zip
# headers = {'User-Agent': config.EMAIL}
# with requests.get(config.URL_SEC_COMPANYFACTS, headers=headers, stream=True) as r:
#     r.raise_for_status()
#     os.makedirs(os.path.dirname(config.ZIP_PATH), exist_ok=True)
#     with open(config.ZIP_PATH, "wb") as f:
#         for chunk in r.iter_content(chunk_size=config.CHUNK_SIZE):
#             if chunk:
#                 f.write(chunk)

def run():
    start_time = time.perf_counter()
    logger = configureLogger()
    cnx = mysql.connector.connect(host=config.MYSQL_HOST, database=config.MYSQL_DATABASE, user=os.getenv("MYSQL_USER"), password=os.getenv("MYSQL_PASSWORD"))
    cursor = cnx.cursor()
    query = ("SELECT CIK FROM companies LIMIT 50;")
    cursor.execute(query)

    ### START A: Use cursor ###
    for cik in cursor:
    ### END A ###

    # ### START B: Use list ###
    # cursor.fetchall() # Need to "use up" cursor
    # ciks = [
    #     # ('0000320193',), # Apple
    #     # ('0000004962',), # American Express
    #     # ('0000012927',), # Boeing
    #     # ('0000034088',), # Exxon Mobil
    #     # ('0001551152',), # AbbVie
    #     ('0000909832',), # Costco
    # ]
    # for cik in ciks:
    # ### END B ###

        cik = cik[0]
        with zipfile.ZipFile(config.ZIP_PATH, 'r') as z:
            fname = 'CIK' + cik + '.json'
            with z.open(fname) as f:
                content = f.read()
                data = json.loads(content.decode('utf-8'))
                fIdToFiscalFinancial = createFIdToFiscalFinancial(data, cik)
                if fIdToFiscalFinancial:
                    getConcepts(cik, data, fIdToFiscalFinancial, logger)
                    handleConceptIssues(cik, fIdToFiscalFinancial, logger)
    cnx.commit()
    cursor.close()
    cnx.close()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    logger.info(f'Elapsed time: {elapsed_time:.2f} seconds')

if __name__ == "__main__":
    run()