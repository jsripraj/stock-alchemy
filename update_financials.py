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
    def __init__(self, concept: str, alias: str, value: str, fiscalYearOfFiling: int = None):
        self.concept: str = concept
        self.alias: str = alias
        self.value: str = value
        self.fiscalYearOfFiling: int = fiscalYearOfFiling

    def __repr__(self):
        return f"FinancialValue('{self.concept}', '{self.alias}', '{self.value}', '{self.fiscalYearOfFiling}')"

class TimespanFinancials:
    def __init__(self, cik: str, cid: str, cy: int, cp: concepts.Period, duration: Enum, end: datetime, accn: str, form: str, fy: str , fp: str, earliest: bool = False):
        self.cik: str = cik
        self.cid: str = cid # Calendar ID: <calendar year>_<calendar period>_<duration>
        self.cy: int = int(cy) # calendar year
        self.cp: concepts.Period = cp # calendar period (indicates end of period, does NOT indicate duration)
        self.duration: Enum = duration
        self.end: datetime = end
        self.accn: str = accn # Accession number
        self.form: str = form
        self.fy: int = fy # Fiscal year
        self.fp: str = fp # Fiscal period (indicates end of period, does NOT indicate duration)
        self.earliest: bool = earliest # indicates whether the period is the earliest reported
        self.values: dict[str, list[FinancialValue]] = defaultdict(list) # concept to values

    def __repr__(self):
        return f"TimespanFinancials(cik: {self.cik}, cid: {self.cid}, cy: {self.cy}, cp: {self.cp}, " + \
               f"duration: {self.duration.name}, " + \
               f"end: {self.end}, accn: {self.accn}, form: {self.form}, " + \
               f"fy: {self.fy}, fp: {self.fp}, earliest: {self.earliest}, values: {pprint.pformat(self.values)}"
    
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
    '''
    Returns calendar year (cp), calendar period (cp), duration
    '''
    cy, cp, duration = cid.split("_")
    return int(cy), concepts.Period[cp], concepts.Duration[duration]

def isDesiredForm(form: str) -> bool:
    return form == '10-K' or form == '10-Q'

def createEndToCid(accnToEntry: dict[str, dict], cik: str) -> dict[datetime, datetime]:
    '''
    Returns a dictionary mapping end date to CID.

    This function uses the maximum duration (e.g. ThreeQuarters for a Q3 period, not OneQuarter).
    CID is <calendar year>_<calendar period>_<duration>. 
    '''
    endToCid: dict[datetime, str] = {}
    entries = [entry for entry in accnToEntry.values()]
    entries.sort(key=lambda e: e['end'], reverse=True)
    for i in range(len(entries)):
        end = strToDate(entries[i]['end'])
        cyqe = getPrecedingCyqe(entries[i-1]['cyqe']) if i > 0 else getMostRecentCyqe(end)
        diff = (end - cyqe).days
        if diff < 0 or diff > 180:
            cyqe = getMostRecentCyqe(end)
        entries[i]['cyqe'] = cyqe

        # use most recent 10-K to get duration (more reliable than fp)
        found = False
        for j in range(i+1, len(entries)):
            if entries[j]['form'] == '10-K':
                found = True
                start = strToDate(entries[j]['end']) + timedelta(days=1)
                duration = getDurationFromDates(start, end)
                break
        # otherwise use fp (can be mislabeled or None)
        if not found:
            if entries[i]['fp']:
                duration = getMaxDurationFromPeriod(concepts.Period[entries[i]['fp']])
            else:
                log(logging.debug, cik, f'Unable to get duration for {end} entry, accn {entries[i]['accn']}')
                continue
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

def createCidToTimespanFinancials(accnToEntry: dict[str, dict], endToCid: dict[datetime, str], cik: str) -> dict[str, TimespanFinancials]:
    '''
    Returns dictionary of CID to a TimespanFinancials with empty values. 

    Creates OneQuarter, TwoQuarters, ThreeQuarters, and Year items for Q1 - Q4, as well as 
    OneQuarter entries for Q2 - Q4. 
    '''
    cidToTimespanFinancials: dict[str, TimespanFinancials] = {}
    entries = [entry for entry in accnToEntry.values()]
    entries.sort(key=lambda entry: entry['end'])
    earliest = True
    for entry in entries:
        end: datetime = strToDate(entry['end'])
        cid = endToCid[end]
        cy, cp, duration = splitCid(cid)
        accn: str = entry['accn']
        form: str = entry['form']
        fy: int = entry['fy']
        fp: concepts.Period = concepts.Period[entry['fp']]
        cidToTimespanFinancials[cid] = TimespanFinancials(cik, cid, cy, cp, duration, end, accn, form, fy, fp, earliest)

        # for Q4, Q3, Q2, create another entry with a OneQuarter duration
        if duration.value > concepts.Duration.OneQuarter.value:
            altDuration = concepts.Duration.OneQuarter
            altCid = createCid(cy, cp, altDuration, cik)
            cidToTimespanFinancials[altCid] = TimespanFinancials(cik, altCid, cy, cp, altDuration, end, None, None, fy, fp, earliest)
        else:
            pass
            earliest = False
    return cidToTimespanFinancials

def getConcepts(cik: str, data: dict, cidToTimespanFinancials: dict[str, TimespanFinancials], endToCid: dict[datetime, str], logger: logging.Logger) -> None:
    # Get max-duration financials
    gaapData = data['facts']['us-gaap']
    for alias in gaapData.keys():
        if alias in concepts.aliasToConcept:
            entries = gaapData[alias]['units']['USD']
            for entry in entries:
                if not isDesiredForm(entry['form']):
                    continue

                # create CID from entry
                end = strToDate(entry['end'])
                if 'start' in entry: 
                    start = strToDate(entry['start'])
                    days = (end - start).days
                    duration = getDurationFromDates(start, end)
                    if duration == concepts.Duration.Other:
                        log(logging.debug, cik, f'in getConcepts {dateToStr(end)} alias {alias} got an "other" duration')
                    if end in endToCid:
                        cy, cp, _ = splitCid(endToCid[end])
                    else:
                        cyqe = getMostRecentCyqe(end)
                        cy, cp = cyqe.year, getPeriod(cyqe)
                    cid = createCid(cy, cp, duration, cik)
                elif end in endToCid: 
                    cid = endToCid[end]
                else:
                    continue

                # if CID matches, add the data
                if cid in cidToTimespanFinancials:
                    concept = concepts.aliasToConcept[alias].name
                    value = entry['val']
                    existingValues = cidToTimespanFinancials[cid].values[concept]
                    fiscalYearOfFiling = int(entry['fy'])
                    newValue = FinancialValue(concept, alias, value, fiscalYearOfFiling)
                    conditionallyAddFinancialValue(existingValues, newValue)
    
    # Get OneQuarter duration financials
    addMissingOneQuarterConcepts(cidToTimespanFinancials, endToCid, cik, logger)

def conditionallyAddFinancialValue(existingValues: list[FinancialValue], newValue: FinancialValue) -> None:
    '''
    Determines how a FinancialValue should be added to a list, then does it. 
    
    The new value can be appended, skipped, or replace an existing element.
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


def addMissingOneQuarterConcepts(cidToTimespanFinancials: dict[str, TimespanFinancials], endToCid: dict[datetime, str], cik: str, logger: logging.Logger) -> None:
    for cid, tf in cidToTimespanFinancials.items():
        if tf.duration == concepts.Duration.OneQuarter:
            for concept in concepts.Concepts:
                concept = concept.name
                values = tf.values[concept]
                if not values:
                    newVal = getOneQuarterValue(cidToTimespanFinancials, endToCid, tf, concept, cik, logger)
                    if newVal != None:
                        values.append(newVal)

def getOneQuarterValue(cidToTf: dict[str, TimespanFinancials], endToCid: dict[datetime, str], tf: TimespanFinancials, concept: str, cik: str, logger: logging.Logger) -> FinancialValue | None:
    longCid = endToCid[tf.end]
    shortCid = getShortCid(longCid, concepts.Duration.OneQuarter, cik, logger)
    if longCid in cidToTf and concept in cidToTf[longCid].values:
        longValues = cidToTf[longCid].values[concept]
        if len(longValues) == 1:
            if shortCid in cidToTf and concept in cidToTf[shortCid].values:
                shortValues = cidToTf[shortCid].values[concept]
                if len(shortValues) == 1:
                    longValue = longValues[0]
                    shortValue = shortValues[0]
                    resConcept = longValue.concept
                    resAlias = longValue.alias
                    resValue = str(int(longValue.value) - int(shortValue.value))
                    return FinancialValue(resConcept, resAlias, resValue)
    return None

def getShortCid(longCid: str, delta: concepts.Duration, cik: str, logger: logging.Logger) -> str | None:
    '''
    Returns the CID from delta duration before the longCid. 
    Returns None if the short CID cannot be calculated.

    delta cannot be greater than or equal to the duration in the longCid.
    For example, given a longCid of 2024_Q3_ThreeQuarters and a delta of OneQuarter, return a CID 
    of 2024_Q2_TwoQuarters. Recall that a CID is <calendar year>_<calendar period>_<duration>
    '''
    longCy, longCp, longDur = splitCid(longCid)
    if delta.value >= longDur.value:
        return None
    shortCy, shortCp = cyMinus(longCy, longCp, delta)
    shortDur = concepts.Duration(longDur.value - delta.value)
    shortCid = createCid(shortCy, shortCp, shortDur, cik)
    return shortCid

def cyMinus(cy: int, cp: concepts.Period, delta: concepts.Duration) -> tuple[int, concepts.Period]:
    '''
    Returns the calendar year (cy) and calendar period (cp) from delta before the given cy and cp:
    '''
    outCp: int = cp.value - delta.value
    if outCp < 0:
        return cy-1, concepts.Period(outCp % 4)
    elif outCp == 0:
        return cy-1, concepts.Period['FY']
    else:
        return cy, concepts.Period(outCp)

# def getLongShortOneQuarterCids(tf: TimespanFinancials, endToCid: dict[datetime, str], logger: logging.Logger) -> tuple[str | None, str | None]:
#     '''
#     Returns long-duration CID and short-duration CID. Returns None, None if given tf does not have 
#     OneQuarter duration.

#     For example, if the given TimespanFinancials is for Q3, the long-duration CID will have Q3 and 
#     ThreeQuarter duration. The short-duration CID will have Q2 and TwoQuarter duration. 
#     Recall that a CID is <calendar year>_<calendar period>_<duration>
#     '''
#     if tf.duration != concepts.Duration.OneQuarter:
#         msg = f'Cannot get long/short-duration CIDs for tf ending {dateToStr(tf.end)}, tf: {tf}'
#         log(logger.warning, tf.cik, msg)
#         return None, None
#     longCid = endToCid[tf.end]
#     shortFp = concepts.FiscalPeriod(ff.fp.value - 1)
#     shortDuration = getMaxDurationFromPeriod(shortFp)
#     shortId = createFId(ff.cik, ff.fy, shortFp, shortDuration)
#     return longId, shortId

def handleConceptIssues(cik: str, cidToTf: dict[str, TimespanFinancials], logger) -> None:
        problemCount = 0
        for cid, tf in cidToTf.items():
            if tf.cy < 2015 or tf.earliest:
                continue
            values = tf.values
            for c in concepts.Concepts:
                concept = c.name
                if len(values[concept]) != 1:
                    msg = f"CID {cid}: at least one concept has zero or multiple values\n{tf}"
                    log(logger.debug, cik, msg)
                    problemCount += 1
                    break
        if problemCount > 0:
            msg = f'{problemCount} problems'
            log(logger.debug, cik, msg)
            jsonFilename = f'CIK{cik}.json'
            extractZipFileToJson(jsonFilename)
        
def getDurationFromDates(start: datetime, end: datetime) -> concepts.Duration:
    days = (end - start).days
    if 60 < days < 120:
        return concepts.Duration.OneQuarter
    if 150 < days < 210:
        return concepts.Duration.TwoQuarters
    if 240 < days < 300:
        return concepts.Duration.ThreeQuarters
    if 310 < days < 400:
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
        # ('0000909832',), # Costco
        # ('0001393818',), # BlackStone
        # ('0001744489',), # Disney
        # ('0001551182',), # Eaton
        ('0000886982',), # Goldman Sachs
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
                    getConcepts(cik, data, cidToTimespanFinancials, endToCid, logger)
                    handleConceptIssues(cik, cidToTimespanFinancials, logger)
            except KeyError as ke:
                log(logging.debug, cik, f'KeyError: {ke}')
    cnx.commit()
    cursor.close()
    cnx.close()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    logger.info(f'Elapsed time: {elapsed_time:.2f} seconds')

if __name__ == "__main__":
    run()