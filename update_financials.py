import requests
import os
import zipfile
import json
import pprint
import mysql.connector
from collections import defaultdict
from datetime import datetime, timedelta
import config
import concepts
from enum import Enum
import logging
import time

class FinancialValue:
    def __init__(self, concept: str, alias: str, value: str, fiscalYearOfFiling: str = None):
        self.concept = concept
        self.alias = alias
        self.value = value
        self.fiscalYearOfFiling = fiscalYearOfFiling

    def __repr__(self):
        return f"FinancialValue('{self.concept}', '{self.alias}', '{self.value}', '{self.fiscalYearOfFiling}')"

class TimespanFinancials:
    def __init__(self, cik: str, cid: str, cy: int, cp: concepts.Period, duration: Enum, end: datetime, accn: str, form: str, fy: str , fp: str):
        self.cik: str = cik
        self.cid: str = cid # Calendar ID: <calendar year>_<calendar period>_<duration>
        self.cy: int = cy, # calendar year
        self.cp: concepts.Period = cp, # calendar period (indicates end of period, does NOT indicate duration)
        self.duration: Enum = duration
        self.end: datetime = end
        self.accn: str = accn # Accession number
        self.form: str = form
        self.fy: int = fy # Fiscal year
        self.fp: str = fp # Fiscal period (indicates end of period, does NOT indicate duration)
        self.values: dict[str, list[FinancialValue]] = defaultdict(list) # concept to values

    def __repr__(self):
        return f"TimespanFinancials(cik: {self.cik}, cid: {self.cid}, cy: {self.cy}, cp: {self.cp}, " + \
               f"duration: {self.duration.name}, " + \
               f"end: {self.end}, accn: {self.accn}, form: {self.form}, " + \
               f"fy: {self.fy}, fp: {self.fp}, values: {pprint.pformat(self.values)}"
    
def strToDate(dateStr: str) -> datetime:
    return datetime.strptime(dateStr, "%Y-%m-%d")

def dateToStr(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")

def createAccnToEntry(data: dict, cik: str) -> dict[datetime, dict] | None:
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
            # Use the most recent fiscal year's entry for each accn
            if (accn not in accnToEntry) or (entry['end'] > accnToEntry[accn]['end']):
                accnToEntry[accn] = entry
    return accnToEntry

def createCidToTimespanFinancials(accnToEntry: dict[str, dict], endToCid: dict[datetime, str], cik: str) -> dict[str, TimespanFinancials]:
    '''
    Returns dictionary of CID to a TimespanFinancials with empty values. 
    Returns None if the dictionary cannot be created.

    Creates OneQuarter, TwoQuarters, ThreeQuarters, and Year items for Q1 - Q4, as well as 
    OneQuarter entries for Q2 - Q4. 
    '''
    cidToTimespanFinancials: dict[str, TimespanFinancials] = {}
    for entry in accnToEntry.values():
        end: datetime = strToDate(entry['end'])
        cid = endToCid[end]
        cy, cp, duration = splitCid(cid)
        accn: str = entry['accn']
        form: str = entry['form']
        fy: int = entry['fy']
        fp: concepts.Period = concepts.Period[entry['fp']]
        cidToTimespanFinancials[cid] = TimespanFinancials(cik, cid, cy, cp, duration, end, accn, form, fy, fp)

        # for Q4, Q3, Q2, create another entry with a OneQuarter duration
        if duration.value > concepts.Duration.OneQuarter.value:
            altDuration = concepts.Duration.OneQuarter
            altCid = createCid(cy, cp, altDuration, cik)
            cidToTimespanFinancials[altCid] = TimespanFinancials(cik, altCid, cy, cp, altDuration, end, None, None, fy, fp)
        else:
            pass
    return cidToTimespanFinancials

def getMaxDurationFromPeriod(fp: concepts.Period | None) -> concepts.Duration:
    if fp == concepts.Period.FY or fp == concepts.Period.Q4:
        return concepts.Duration.Year
    if fp == concepts.Period.Q3:
        return concepts.Duration.ThreeQuarters
    if fp == concepts.Period.Q2:
        return concepts.Duration.TwoQuarters
    if fp == concepts.Period.Q1:
        return concepts.Duration.OneQuarter
    return concepts.Duration.Other

def getPeriod(cyqe: datetime) -> concepts.Period:
    return concepts.Period(cyqe.month // 3)

def createCid(cy: int, cp: concepts.Period, duration: concepts.Duration, cik: str) -> str:
    '''
    Returns a Calendar ID (cid): <calendar year>_<calendar period>_<duration>

    For example: 2023_Q3_OneQuarter
    '''
    try:
        return "_".join([str(cy), cp.name, duration.name])
    except TypeError as e:
        log(logging.debug, cik, f'createFId: {e}')
        return None

def splitCid(cid: str) -> tuple[int, concepts.Period, concepts.Duration]:
    cy, cp, duration = cid.split("_")
    return int(cy), concepts.Period[cp], concepts.Duration[duration]

def isDesiredForm(form: str) -> bool:
    return form == '10-K' or form == '10-Q'

def createEndToCid(accnToEntry: dict[str, dict], cik: str) -> dict[datetime, datetime] | None:
    ends: list[datetime] = [strToDate(entry['end']) for entry in accnToEntry.values()]
    ends.sort(reverse=True)
    cyqes: list[datetime] = [None] * len(ends) # Calendar year quarter ends
    cyqes[0] = getMostRecentCyqe(ends[0])
    for i in range(1, len(ends)):
        cyqe = getPrecedingCyqe(cyqes[i-1])
        end = ends[i]
        diff = (end - cyqe).days
        if diff < 0 or diff > 90:
            cyqe = getMostRecentCyqe(ends[i])
        cyqes[i] = cyqe
    endToCyqe: dict[datetime, datetime] = {ends[i]: cyqes[i] for i in range(len(ends))}

    endToCid: dict[datetime, str] = {}
    for accn, entry in accnToEntry.items():
        end: datetime = strToDate(entry['end'])
        cyqe: datetime = endToCyqe[end]
        fp: concepts.Period = concepts.Period[entry['fp']]
        if not fp:
            log(logging.debug, cik, f'fp is None for {end} Assets in accn {accn}')
        duration: concepts.Duration = getMaxDurationFromPeriod(fp)
        cy: int = cyqe.year
        cp: concepts.Period = getPeriod(cyqe)
        cid = createCid(cy, cp, duration, cik)
        endToCid[end] = cid
    return endToCid

def getMostRecentCyqe(date: datetime) -> datetime:
    y = date.year
    if date < datetime(y, 3, 31):
        return datetime(y-1, 12, 31)
    if date < datetime(y, 6, 30):
        return datetime(y, 3, 31)
    if date < datetime(y, 9, 30):
        return datetime(y, 6, 30)
    if date < datetime(y, 12, 31):
        return datetime(y, 9, 30)
    return datetime(y, 12, 31)

def getPrecedingCyqe(cyqe: datetime) -> datetime:
    return getMostRecentCyqe(cyqe - timedelta(days=1))

def getConcepts(cik: str, data: dict, fIdToTimespanFinancials: dict, logger: logging.Logger) -> None:
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
                if entryId in fIdToTimespanFinancials:
                    concept = concepts.aliasToConcept[alias].name
                    value = entry['val']
                    existingValues = fIdToTimespanFinancials[entryId].values[concept]
                    fiscalYearOfFiling = entry['fy']
                    newValue = FinancialValue(concept, alias, value, fiscalYearOfFiling)
                    addFinancialValue(existingValues, newValue)
    addMissingOneQuarterConcepts(fIdToTimespanFinancials, logger)

def addFinancialValue(existingValues: list[FinancialValue], newValue: FinancialValue) -> None:
    '''
    Determines whether and how a FinancialValue should be added to a list, then adds it if necessary.
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
        if replaceFinancialValue(existingValues[i], newValue):
            existingValues[i] = newValue

    return

def replaceFinancialValue(A: FinancialValue, B: FinancialValue) -> bool:
    '''
    Returns True if FinancialValue A should be replaced by B. 
    
    A should be replaced by B if B is more recent (or at least not None).
    '''
    if B.fiscalYearOfFiling and (not A.fiscalYearOfFiling or B.fiscalYearOfFiling > A.fiscalYearOfFiling):
        return True

    return False


def addMissingOneQuarterConcepts(fIdToTimespanFinancials: dict, logger: logging.Logger) -> None:
    '''
    Add missing one-quarter-duration concepts. 

    For example, fourth quarter concepts could be missing if they are not reported and must 
    be derived. Also, cash flow concepts could be missing for Q2 and Q3 since they might be 
    reported only in two- and three-quarter durations. 
    '''
    for fId, ff in fIdToTimespanFinancials.items():
        if ff.duration == concepts.Duration.OneQuarter and ff.fp != concepts.FiscalPeriod.Q1:
            for concept in concepts.Concepts:
                concept = concept.name
                values = ff.values[concept]
                if not values:
                    value = getOneQuarterValue(fIdToTimespanFinancials, ff, concept, logger)
                    if value != None:
                        values.append(value)

def getOneQuarterValue(fIdToFf: dict[str, TimespanFinancials], ff: TimespanFinancials, concept: str, logger: logging.Logger) -> FinancialValue | None:
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
                    return FinancialValue(resConcept, resAlias, resValue)
    return None

def getLongShortOneQuarterFIds(ff: TimespanFinancials, logger: logging.Logger) -> tuple[str | None, str | None]:
    '''
    Returns long-duration fId and short-duration fId.

    For example, if the given TimespanFinancials is for Q3, the long-duration will fId have Q3 and 
    ThreeQuarter duration. The short-duration fId will have Q2 and TwoQuarter duration. 
    This function should only be used on one-quarter duration TimespanFinancialss.
    '''
    if ff.duration != concepts.Duration.OneQuarter:
        msg = f'Cannot get long/short-duration FId of {ff.fp.name} fiscal period, FF: {ff}'
        log(logger.warning, ff.cik, msg)
        return None, None
    longDuration = getMaxDurationFromPeriod(ff.fp)
    longId = createFId(ff.cik, ff.fy, ff.fp, longDuration)
    shortFp = concepts.FiscalPeriod(ff.fp.value - 1)
    shortDuration = getMaxDurationFromPeriod(shortFp)
    shortId = createFId(ff.cik, ff.fy, shortFp, shortDuration)
    return longId, shortId

def handleConceptIssues(cik: str, fIdToTimespanFinancials: dict, logger) -> None:
        problemCount = 0
        for fId, ff in fIdToTimespanFinancials.items():
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
    query = ("SELECT CIK FROM companies;")
    cursor.execute(query)

    ### START A: Use cursor ###
    # for cik in cursor:
    ### END A ###

    # ### START B: Use list ###
    cursor.fetchall() # Need to "use up" cursor
    ciks = [
        # ('0000320193',), # Apple
        # ('0000004962',), # American Express
        # ('0000012927',), # Boeing
        # ('0000034088',), # Exxon Mobil
        # ('0001551152',), # AbbVie
        ('0000909832',), # Costco
    ]
    for cik in ciks:
    # ### END B ###

        cik = cik[0]
        with zipfile.ZipFile(config.ZIP_PATH, 'r') as z:
            fname = 'CIK' + cik + '.json'
            try:
                with z.open(fname) as f:
                    content = f.read()
                    data = json.loads(content.decode('utf-8'))
                    accnToEntry = createAccnToEntry(data, cik)
                    if not accnToEntry:
                        continue
                    endToCid: dict[datetime, str] = createEndToCid(accnToEntry, cik)
                    cidToTimespanFinancials: dict[str, TimespanFinancials] = createCidToTimespanFinancials(accnToEntry, endToCid, cik)
                    # fIdToTimespanFinancials = createFIdToTimespanFinancials(data, cik)
                    if fIdToTimespanFinancials:
                        getConcepts(cik, data, fIdToTimespanFinancials, logger)
                        handleConceptIssues(cik, fIdToTimespanFinancials, logger)
            except KeyError as ke:
                log(logging.debug, cik, ke)
    cnx.commit()
    cursor.close()
    cnx.close()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    logger.info(f'Elapsed time: {elapsed_time:.2f} seconds')

if __name__ == "__main__":
    run()