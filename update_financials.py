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
        list[FinancialPeriod] | None - a list of FinancialPeriod objects filled out with data and 
        sorted in chronological order. Returns None if the list cannot be created.
    """
    if not checkData(data, cik, logger):
        return None

    # Create list of FinancialPeriods sorted chronologically
    entries = data['facts']['us-gaap']['Assets']['units']['USD']
    processed = processEntries(entries)
    endToFinancialPeriod = {}
    for e in processed:
        if isDesiredForm(e['form']):
            endToFinancialPeriod[strToDate(e['end'])] = FinancialPeriod(cik, strToDate(e['end']))
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
    if not any(isDesiredForm(entry['form']) for entry in data):
        log(logger.debug, cik, f'No desired forms found')
        return False
    return True
    
def processEntries(entries: list[dict]):
    '''
    Removes entries with duplicate (or one-day-apart) dates or undesired forms.
    '''
    processed = []
    entriesSorted = sorted(entries, key=lambda e: e['end'])
    for i in range(len(entriesSorted)):
        entry = entriesSorted[i]
        if not isDesiredForm(entry['form']):
            continue
        # If two dates are only one day apart, skip the later one
        if processed:
            prev = strToDate(processed[-1]['end'])
            cur = strToDate(entry['end'])
            diff = (cur - prev).days
            if diff <= 1:
                continue
        processed.append(entry)
    return processed

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

def isDesiredForm(form: str) -> bool:
    return form == '10-K' or form == '10-Q'

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

def getPeriod(cyqe: datetime) -> concepts.Period:
    return concepts.Period(cyqe.month // 3)

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

def addMissingOneQuarterConcepts(fps: list[FinancialPeriod], cik: str, logger: logging.Logger) -> None:
    '''
    Parameters
    fps: list[FinancialPeriod]
        A list of FinancialPeriods sorted in chronological order
    '''
    for i in range(1, len(fps)):
        fp = fps[i]
        for concept, fvs in fp.conceptToFinancialValues.items():
            alreadyHas = any(fv.duration == concepts.Duration.OneQuarter for fv in fvs)
            noNeed = any(fv.duration == None for fv in fvs)
            if alreadyHas or noNeed:
                continue
            for fv in fvs:
                if fv.duration == concepts.Duration.Other:
                    continue
                oldFp = fps[i-1]
                oldFvs = oldFp.conceptToFinancialValues[concept]
                prevFv = next((oldFv for oldFv in oldFvs if oldFv.duration and oldFv.duration.value == fv.duration.value - 1), None)
                if prevFv:
                    fvs.append(FinancialValue(concept, fv.alias, fv.value - prevFv.value, duration=concepts.Duration.OneQuarter))
                    break
    return

def handleConceptIssues(cik: str, fps: list[FinancialPeriod], logger) -> int:
    '''
    Returns:
        int: 1 if there are issues, 0 if no issues

    Parameters:
        fps: list[FinancialPeriod] - a list of populated FinancialPeriods, sorted chronologically.
    '''
    problemCount = 0
    for i in range(2, len(fps)):
        fp = fps[i]
        if fp.cy < datetime.today().year - 10:
            continue
        for c in concepts.Concept:
            concept = c.name
            fvs = fp.conceptToFinancialValues[concept]
            pre = f'{dateToStr(fp.end)} {concept}'
            msg = None
            if not fvs:
                msg = f"{pre}: no FinancialValues"
            elif len(fvs) == 1 and fvs[0].duration != concepts.Duration.OneQuarter:
                msg = f"{pre} ({fvs[0].alias}): one value but with {fvs[0].duration.name} duration"
            elif len(fvs) > 1 and not any(fv.duration != concepts.Duration.OneQuarter for fv in fvs):
                msg = f"{pre}: {len(fvs)} values but none with OneQuarter duration"
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
    for cik in cursor:
    ### END A ###

    # ### START B: Use list ###
    # cursor.fetchall() # Need to "use up" cursor
    # ciks = [
    #     # ('0001551152',), # AbbVie
    #     # ('0000002488',), # Advanced Micro Devices
    #     # ('0001018724',), # Amazon
    #     # ('0000004962',), # American Express
    #     # ('0000320193',), # Apple
    #     # ('0001973239',), # ARM Holdings
    #     # ('0001393818',), # BlackStone
    #     # ('0001730168',), # Broadcom
    #     # ('0000012927',), # Boeing
    #     # ('0000858877',), # Cisco
    #     # ('0000909832',), # Costco
    #     # ('0000315189',), # Deere
    #     # ('0001744489',), # Disney
    #     # ('0001551182',), # Eaton
    #     # ('0000034088',), # Exxon Mobil
    #     # ('0000886982',), # Goldman Sachs
    #     # ('0001707925',), # Linde
    #     ('0000064040',), # S&P Global
    #     # ('0001594805',), # Shopify
    # ]
    # for cik in ciks:
    # ### END B ###

        cik = cik[0]
        with zipfile.ZipFile(config.ZIP_PATH, 'r') as z:
            fname = 'CIK' + cik + '.json'
            try:
                with z.open(fname) as f:
                    content = f.read()
                    data = json.loads(content.decode('utf-8'))
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