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
import shutil

class FinancialValue:
    def __init__(self, concept: concepts.Concept, alias: str, value: int, filingFiscalYear: int = None, duration: concepts.Duration = None):
        self.concept: concepts.Concept = concept
        self.alias: str = alias
        self.value: int = value
        self.filingFiscalYear: int = filingFiscalYear
        self.duration: concepts.Duration = duration
    
    def __eq__(self, other):
        return self.concept == other.concept and self.value == other.value and self.duration == other.duration

    def __repr__(self):
        return f"FinancialValue(concept: {self.concept}, alias: {self.alias}, value: {self.value}, " \
            f"filing FY: {self.filingFiscalYear}, duration: {self.duration.name if self.duration else None})"

class FinancialPeriod:
    def __init__(self, cik: str, end: datetime):
        self.cik: str = cik
        self.end: datetime = end
        self.cy: int = None # calendar year
        self.cp: concepts.Period = None # calendar period (indicates end of period, does NOT indicate duration)
        self.conceptToFinancialValues: dict[str, list[FinancialValue]] = defaultdict(list)

    def __repr__(self):
        return f"FinancialPeriod(cik: {self.cik}, cy: {self.cy}, cp: {self.cp}, " + \
               f"end: {self.end}, " + \
               f"conceptToFinancialValues: {pprint.pformat(self.conceptToFinancialValues)}"

def createFinancialPeriods(data: dict, cik: str, logger) -> list[FinancialPeriod] | None:
    """
    Returns:
        list[FinancialPeriod] - a list of FinancialPeriod objects filled out with data and sorted 
        in chronological order.
    """
    if not checkData(data, cik, logger):
        return None

    # Create list of FinancialPeriods sorted chronologically
    entries = data['facts']['us-gaap']['Assets']['units']['USD']
    endToFinancialPeriod = {strToDate(e['end']): FinancialPeriod(cik, strToDate(e['end'])) for e in entries}
    financialPeriods = [fp for fp in endToFinancialPeriod.values()]
    addCalendarAttributes(financialPeriods)
    financialPeriods.sort(key=lambda fp: fp.end)

    # Add FinancialValues
    for alias, metadata in data['facts']['us-gaap'].items():
        if alias not in concepts.aliasToConcept:
            continue
        entries = metadata['units']['USD']
        entries.sort(key=lambda e: e['end'])
        for entry in entries:
            if not isDesiredForm(entry['form']):
                continue
            end = strToDate(entry['end'])
            if end not in endToFinancialPeriod:
                continue
            fp = endToFinancialPeriod[end]
            concept: concepts.Concept = concepts.aliasToConcept[alias]
            value = int(entry['val'])
            filingFY = int(entry['fy']) if entry['fy'] else None
            value = FinancialValue(concept, alias, value, filingFY)
            if 'start' in entry:
                value.duration = getDurationFromDates(strToDate(entry['start']), end)
            existing: list[FinancialValue] = fp.conceptToFinancialValues[concept.name]
            conditionallyAddFinancialValue(existing, value)
    
    # Get OneQuarter duration financials
    addMissingOneQuarterConcepts(financialPeriods, cik, logger)
    return financialPeriods

def checkData(data: dict, cik: str, logger) -> bool:
    '''
    Determines if the raw data is usable.

    Returns:
        bool: True if data is usable, else False.
    '''
    for key in ['facts', 'us-gaap', 'Assets', 'units', 'USD']:
        if key not in data:
            log(logger.debug, cik, f'"{key}" not found in JSON')
            return False
        data = data[key]
    return True
    
def addCalendarAttributes(fps: list[FinancialPeriod]) -> None:
    '''
    Adds calendar year and calendar period to each item in a list of FinancialPeriods.
    '''
    fpsReverseChronological = sorted(fps, key=lambda fp: fp.end, reverse=True)
    cyqes = [None] * len(fpsReverseChronological)
    for i in range(len(fpsReverseChronological)):
        fp = fpsReverseChronological[i]
        cyqe = getCyqePriorTo(cyqes[i-1]) if i > 0 else getMostRecentCyqe(fp.end)
        diff = (fp.end - cyqe).days
        if diff < 0 or diff > 180:
            cyqe = getMostRecentCyqe(fp.end)
        fp.cy = cyqe.year
        fp.cp = getPeriod(cyqe)
        cyqes[i] = cyqe

def strToDate(dateStr: str) -> datetime:
    return datetime.strptime(dateStr, "%Y-%m-%d")

def dateToStr(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")

# def createAccnToEntry(data: dict, cik: str) -> dict[datetime, dict] | None:
#     if 'facts' not in data:
#         log(logging.debug, cik, f'"facts" not found in JSON')
#         return None
#     if 'us-gaap' not in data['facts']:
#         log(logging.debug, cik, f'"us-gaap" not found in JSON')
#         return None
#     if 'Assets' not in data['facts']['us-gaap']:
#         log(logging.debug, cik, f'"Assets" not found in JSON')
#         return None
#     if 'units' not in data['facts']['us-gaap']['Assets']:
#         log(logging.debug, cik, f'"units" not found in JSON')
#         return None
#     if 'USD' not in data['facts']['us-gaap']['Assets']['units']:
#         log(logging.debug, cik, f'"USD" not found in JSON')
#         return None

#     accnToEntry = {}
#     for entry in data['facts']['us-gaap']['Assets']['units']['USD']:
#         if isDesiredForm(entry['form']):
#             accn = entry['accn']
#             # Use the most recent fiscal year's entry for each accn
#             if (accn not in accnToEntry) or (entry['end'] > accnToEntry[accn]['end']):
#                 accnToEntry[accn] = entry
#     return accnToEntry

def isDesiredForm(form: str) -> bool:
    return form == '10-K' or form == '10-Q'

# def createEndToCid(accnToEntry: dict[str, dict], cik: str) -> dict[datetime, datetime]:
#     '''
#     Returns a dictionary mapping end date to CID.

#     This function uses the maximum duration (e.g. ThreeQuarters for a Q3 period, not OneQuarter).
#     CID is <calendar year>_<calendar period>_<duration>. 
#     '''
#     endToCid: dict[datetime, str] = {}
#     entries = [entry for entry in accnToEntry.values()]
#     entries.sort(key=lambda e: e['end'])
#     for i in range(len(entries)):
#         end = strToDate(entries[i]['end'])
#         cyqe = getCyqePriorTo(entries[i-1]['cyqe']) if i > 0 else getMostRecentCyqe(end)
#         diff = (end - cyqe).days
#         if diff < 0 or diff > 180:
#             cyqe = getMostRecentCyqe(end)
#         entries[i]['cyqe'] = cyqe
#         duration = getDuration(entries, i, endToCid, cik)
#         cy: int = cyqe.year
#         cp: concepts.Period = getPeriod(cyqe)
#         cid = createCid(cy, cp, duration, cik)
#         endToCid[end] = cid
#     return endToCid

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

def getCyqePriorTo(cyqe: datetime) -> datetime:
    return getMostRecentCyqe(cyqe - timedelta(days=1))

# def getDuration(entries: list[dict], i: int, endToCid: dict[datetime, str], cik: str) -> concepts.Duration:
#     '''
#     Returns a duration for the i'th entry in entries.
    
#     Obtaining the correct duration can sometimes be tricky when data is mislabeled or missing. 
#     This function uses multiple different methods to get a duration, and returns the most popular result.

#     Parameters
#     entries: list[dict]
#         A list of a concept's data entries, sorted in chronological order by 'end'.
    
#     i: int
#         The index of the entry to find the duration for.
    
#     endToCid: dict[datetime, str]
#         Maps from end to CID.
#     '''
#     points: dict[concepts.Duration, int] = defaultdict(int)
#     end = strToDate(entries[i]['end'])

#     # use most recent 10-K to get duration (form can be mislabeled, but more reliable than fp)
#     for j in range(i-1, -1, -1):
#         if entries[j]['form'] == '10-K':
#             start = strToDate(entries[j]['end']) + timedelta(days=1)
#             tenKduration = getDurationFromDates(start, end)
#             points[tenKduration] += 1
#             break

#     # use most recent period to get duration
#     if i > 0:
#         prevCid = endToCid[strToDate(entries[i-1]['end'])]
#         _, _, prevDur = splitCid(prevCid)
#         if prevDur == concepts.Duration.ThreeQuarters:
#             mrpDuration = concepts.Duration.Year
#         else:
#             mrpDuration = concepts.Duration((prevDur.value + 1) % 4)
#         points[mrpDuration] += 1

#     # use fp (can be mislabeled or None)
#     if entries[i]['fp']:
#         fpDuration = getMaxDurationFromPeriod(concepts.Period[entries[i]['fp']])
#         points[fpDuration] += 1
    
#     # find strict max
#     # find max points
#     maxPoints = max(points.values())
#     # find the duration with that many points
#     # if there are two durations, there is no strict max
#     finalDur = None
#     for dur, pts in points.items():
#         if pts == maxPoints:
#             if finalDur == None:
#                 finalDur = dur
#             else:
#                 msg = f'in getDuration, unable to calculate duration, returning "other" for {end} entry, accn {entries[i]['accn']}'
#                 log(logging.debug, cik, msg)
#                 return concepts.Duration.Other
    
#     return finalDur

# def getMaxDurationFromPeriod(fp: concepts.Period | None) -> concepts.Duration:
#     if fp == concepts.Period.FY or fp == concepts.Period.Q4:
#         return concepts.Duration.Year
#     if fp == concepts.Period.Q3:
#         return concepts.Duration.ThreeQuarters
#     if fp == concepts.Period.Q2:
#         return concepts.Duration.TwoQuarters
#     if fp == concepts.Period.Q1:
#         return concepts.Duration.OneQuarter
#     return concepts.Duration.Other

def getPeriod(cyqe: datetime) -> concepts.Period:
    return concepts.Period(cyqe.month // 3)

# def createCid(cy: int, cp: concepts.Period, duration: concepts.Duration, cik: str) -> str:
#     '''
#     Returns a Calendar ID (cid): <calendar year>_<calendar period>_<duration>

#     For example: 2023_Q3_OneQuarter
#     '''
#     try:
#         return "_".join([str(cy), cp.name, duration.name])
#     except TypeError as e:
#         log(logging.debug, cik, f'createFId: {e}')
#         return None

# def splitCid(cid: str) -> tuple[int, concepts.Period, concepts.Duration]:
#     '''
#     Returns calendar year (cy), calendar period (cp), duration
#     '''
#     cy, cp, duration = cid.split("_")
#     return int(cy), concepts.Period[cp], concepts.Duration[duration]

# def createCidToTimespanFinancials(accnToEntry: dict[str, dict], endToCid: dict[datetime, str], cik: str) -> dict[str, TimespanFinancials]:
#     '''
#     Returns dictionary of CID to a TimespanFinancials with empty values. 

#     Creates OneQuarter, TwoQuarters, ThreeQuarters, and Year items for Q1 - Q4, as well as 
#     OneQuarter entries for Q2 - Q4. 
#     '''
#     cidToTimespanFinancials: dict[str, TimespanFinancials] = {}
#     entries = [entry for entry in accnToEntry.values()]
#     entries.sort(key=lambda entry: entry['end'])
#     earliest = True
#     for entry in entries:
#         end: datetime = strToDate(entry['end'])
#         cid = endToCid[end]
#         cy, cp, duration = splitCid(cid)
#         accn: str = entry['accn']
#         form: str = entry['form']
#         fy: int = entry['fy']
#         fp: concepts.Period = concepts.Period[entry['fp']]
#         cidToTimespanFinancials[cid] = TimespanFinancials(cik, cid, cy, cp, duration, end, accn, form, fy, fp, earliest)

#         # for Q4, Q3, Q2, create another entry with a OneQuarter duration
#         if duration.value > concepts.Duration.OneQuarter.value:
#             altDuration = concepts.Duration.OneQuarter
#             altCid = createCid(cy, cp, altDuration, cik)
#             cidToTimespanFinancials[altCid] = TimespanFinancials(cik, altCid, cy, cp, altDuration, end, None, None, fy, fp, earliest)
#         else:
#             pass
#             earliest = False
#     return cidToTimespanFinancials

# def getConcepts(cik: str, data: dict, cidToTimespanFinancials: dict[str, TimespanFinancials], endToCid: dict[datetime, str], logger: logging.Logger) -> None:
#     # Get max-duration financials
#     gaapData = data['facts']['us-gaap']
#     for alias in gaapData.keys():
#         if alias in concepts.aliasToConcept:
#             entries = gaapData[alias]['units']['USD']
#             for entry in entries:
#                 if not isDesiredForm(entry['form']):
#                     continue

#                 # create CID from entry
#                 end = strToDate(entry['end'])
#                 if 'start' in entry: 
#                     start = strToDate(entry['start'])
#                     days = (end - start).days
#                     duration = getDurationFromDates(start, end)
#                     if duration == concepts.Duration.Other:
#                         log(logging.debug, cik, f'in getConcepts {dateToStr(end)} alias {alias} got an "other" duration')
#                     if end in endToCid:
#                         cy, cp, _ = splitCid(endToCid[end])
#                     else:
#                         cyqe = getMostRecentCyqe(end)
#                         cy, cp = cyqe.year, getPeriod(cyqe)
#                     cid = createCid(cy, cp, duration, cik)
#                 elif end in endToCid: 
#                     cid = endToCid[end]
#                 else:
#                     continue

#                 # if CID matches, add the data
#                 if cid in cidToTimespanFinancials:
#                     concept = concepts.aliasToConcept[alias].name
#                     value = int(entry['val'])
#                     existingValues = cidToTimespanFinancials[cid].values[concept]
#                     fiscalYearOfFiling = int(entry['fy'])
#                     newValue = FinancialValue(concept, alias, value, fiscalYearOfFiling)
#                     conditionallyAddFinancialValue(existingValues, newValue)
    
#     # Get OneQuarter duration financials
#     addMissingOneQuarterConcepts(cidToTimespanFinancials, endToCid, cik, logger)
#     return

def conditionallyAddFinancialValue(existingValues: list[FinancialValue], newValue: FinancialValue) -> None:
    '''
    Determines whether and how a FinancialValue should be added to a list, then does it. 
    
    The new value can be appended, skipped, or replace an existing element.
    '''
    # If the list is empty, append it
    if not existingValues:
        existingValues.append(newValue)
        return
    
    # If the duration doesn't exist, append it
    if not any(ev.duration == newValue.duration for ev in existingValues):
        existingValues.append(newValue)
        return

    # Replace if "better"
    for i in range(len(existingValues)):
        exist = existingValues[i]
        if exist.duration == newValue.duration and newValue.filingFiscalYear:
            if (not exist.filingFiscalYear) or newValue.filingFiscalYear > exist.filingFiscalYear:
                existingValues[i] = newValue

    return

# def replaceFinancialValue(A: FinancialValue, B: FinancialValue) -> bool:
#     '''
#     Returns True if FinancialValue A should be replaced by B. 
    
#     A should be replaced by B if B is more recent (or at least not None).
#     '''
#     if B.fiscalYearOfFiling and (not A.fiscalYearOfFiling or B.fiscalYearOfFiling > A.fiscalYearOfFiling):
#         return True

#     return False


def addMissingOneQuarterConcepts(fps: list[FinancialPeriod], cik: str, logger: logging.Logger) -> None:
    '''
    Parameters
    fps: list[FinancialPeriod]
        A list of FinancialPeriods sorted in chronological order
    '''
    for i in range(1, len(fps)):
        for concept, fvs in fps[i].conceptToFinancialValues.items():
            alreadyHas = any(fv.duration == concepts.Duration.OneQuarter for fv in fvs)
            noNeed = any(fv.duration == None for fv in fvs)
            if alreadyHas or noNeed:
                continue
            # found = False
            for fv in fvs:
                if fv.duration == concepts.Duration.Other:
                    continue
                oldFvs = fps[i-1].conceptToFinancialValues[concept]
                # check if prevFp has a value with duration oneQuarter less than fv
                prevFv = next((oldFv for oldFv in oldFvs if oldFv.duration and oldFv.duration.value == fv.duration.value - 1), None)
                if prevFv:
                    fvs.append(FinancialValue(concept, fv.alias, fv.value - prevFv.value, duration=concepts.Duration.OneQuarter))
                    # found = True
                    break
            # if not found:
            #     msg = f"{fps[i].end} {concept}: Unable to get OneQuarter value {fps[i]}"
            #     log(logger.debug, cik, msg)
    return

# def getOneQuarterValue(cidToTf: dict[str, TimespanFinancials], endToCid: dict[datetime, str], tf: TimespanFinancials, concept: str, cik: str, logger: logging.Logger) -> FinancialValue | None:
#     longCid = endToCid[tf.end]
#     shortCid = getShortCid(longCid, concepts.Duration.OneQuarter, cik, logger)
#     if longCid in cidToTf and concept in cidToTf[longCid].values:
#         longValues = cidToTf[longCid].values[concept]
#         if len(longValues) == 1:
#             if shortCid in cidToTf and concept in cidToTf[shortCid].values:
#                 shortValues = cidToTf[shortCid].values[concept]
#                 if len(shortValues) == 1:
#                     longValue = longValues[0]
#                     shortValue = shortValues[0]
#                     resConcept = longValue.concept
#                     resAlias = longValue.alias
#                     resValue = longValue.value - shortValue.value
#                     return FinancialValue(resConcept, resAlias, resValue)
#     return None

# def getShortCid(longCid: str, delta: concepts.Duration, cik: str, logger: logging.Logger) -> str | None:
#     '''
#     Returns the CID from delta duration before the longCid. 
#     Returns None if the short CID cannot be calculated.

#     delta cannot be greater than or equal to the duration in the longCid.
#     For example, given a longCid of 2024_Q3_ThreeQuarters and a delta of OneQuarter, return a CID 
#     of 2024_Q2_TwoQuarters. Recall that a CID is <calendar year>_<calendar period>_<duration>
#     '''
#     longCy, longCp, longDur = splitCid(longCid)
#     if delta.value >= longDur.value:
#         return None
#     shortCy, shortCp = cyMinus(longCy, longCp, delta)
#     shortDur = concepts.Duration(longDur.value - delta.value)
#     shortCid = createCid(shortCy, shortCp, shortDur, cik)
#     return shortCid

# def cyMinus(cy: int, cp: concepts.Period, delta: concepts.Duration) -> tuple[int, concepts.Period]:
#     '''
#     Returns the calendar year (cy) and calendar period (cp) from delta before the given cy and cp:
#     '''
#     outCp: int = cp.value - delta.value
#     if outCp < 0:
#         return cy-1, concepts.Period(outCp % 4)
#     elif outCp == 0:
#         return cy-1, concepts.Period['FY']
#     else:
#         return cy, concepts.Period(outCp)

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

def handleConceptIssues(cik: str, fps: list[FinancialPeriod], logger) -> int:
    '''
    Returns:
        int: 1 if there are issues, 0 if no issues

    Parameters:
        fps: list[FinancialPeriod] - a list of populated FinancialPeriods, sorted chronologically.
    '''
    problemCount = 0
    for i in range(1, len(fps)):
        fp = fps[i]
        if fp.cy < datetime.today().year - 10:
            continue
        for c in concepts.Concept:
            concept = c.name
            fvs = fp.conceptToFinancialValues[concept]
            msg = None
            pre = f'{dateToStr(fp.end)} {concept}'
            if not fvs:
                msg = f"{pre}: no FinancialValues"
            elif len(fvs) == 1 and fvs[0].duration != concepts.Duration.OneQuarter:
                msg = f"{pre}: one value but with {fvs[0].duration.name} duration"
            elif len(fvs) > 1 and not any(fv.duration != concepts.Duration.OneQuarter for fv in fvs):
                msg = f"{pre}: {len(fvs)} values but none with OneQuarter duration"
            # elif len(fvs) == 2 and fvs[0].duration != concepts.Duration.OneQuarter and fvs[1].duration != concepts.Duration.OneQuarter:
            #     msg = f"{pre}: 2 values but with {fvs[0].duration.name} and {fvs[1].duration.name} durations"
            if msg:
                log(logger.debug, cik, msg)
                problemCount += 1
    if problemCount > 0:
        msg = f'{problemCount} problems'
        log(logger.debug, cik, msg)
        jsonFilename = f'CIK{cik}.json'
        extractZipFileToJson(jsonFilename)
        return 1
    return 0
        
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
    logging.basicConfig(filename=config.LOG_PATH,
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
    query = ("SELECT CIK FROM companies LIMIT 100;")
    cursor.execute(query)
    problemCikCount = 0

    ### START A: Use cursor ###
    # for cik in cursor:
    ### END A ###

    # ### START B: Use list ###
    cursor.fetchall() # Need to "use up" cursor
    ciks = [
        # ('0001551152',), # AbbVie
        # ('0000002488',), # Advanced Micro Devices
        ('0001018724',), # Amazon
        # ('0000004962',), # American Express
        # ('0000320193',), # Apple
        # ('0001393818',), # BlackStone
        # ('0000012927',), # Boeing
        # ('0000909832',), # Costco
        # ('0001744489',), # Disney
        # ('0001551182',), # Eaton
        # ('0000034088',), # Exxon Mobil
        # ('0000886982',), # Goldman Sachs
        # ('0000064040',), # S&P Global
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
                    # accnToEntry = createAccnToEntry(data, cik)
                    # if not accnToEntry:
                    #     continue
                    # endToCid: dict[datetime, str] = createEndToCid(accnToEntry, cik)
                    # cidToTimespanFinancials: dict[str, TimespanFinancials] = createCidToTimespanFinancials(accnToEntry, endToCid, cik)
                    # getConcepts(cik, data, cidToTimespanFinancials, endToCid, logger)
                    # endToTimespanFinancials = createEndToTimespanFinancials(data, cik)
                    # if not endToTimespanFinancials:
                    #     continue
                    fps: list[FinancialPeriod] = createFinancialPeriods(data, cik, logger)
                    if fps:
                        problemCikCount += handleConceptIssues(cik, fps, logger)
            except KeyError as ke:
                log(logger.debug, cik, f'KeyError: {ke}')
    
    cnx.commit()
    cursor.close()
    cnx.close()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    logger.debug(f"{problemCikCount} CIKs with issues")
    logger.info(f'Elapsed time: {elapsed_time:.2f} seconds')
    shutil.copyfile(config.LOG_PATH, os.path.join(config.LOG_DIR, "copy.log"))

if __name__ == "__main__":
    run()