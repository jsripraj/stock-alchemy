import requests
import os
import zipfile
import json
from pprint import pp
import mysql.connector
from collections import defaultdict
import datetime
import config
import concepts
from enum import Enum

class FiscalValue:
    def __init__(self, concept: str, alias: str, value: str, filingFy: str = None):
        self.concept = concept
        self.alias = alias
        self.value = value
        self.filingFy = filingFy

    def __repr__(self):
        return f"FiscalValue('{self.concept}', '{self.alias}', '{self.value}', '{self.filingFy}')"

class FiscalFinancial:
    def __init__(self, cik: str, fId: str, duration: Enum, start: str, end: str, accn: str, form: str, fy: str , fp: str):
        self.cik: str = cik
        self.fId: str = fId # fiscal ID
        self.duration: Enum = duration
        self.start: str = start
        self.end: str = end
        self.accn: str = accn # Accession number
        self.form: str = form
        self.fy: str = fy
        self.fp: str = fp
        self.values: dict[str, list[FiscalValue]] = defaultdict(list) # concept to values
    
def strToDate(dateStr: str) -> datetime:
    return datetime.datetime.strptime(dateStr, "%Y-%m-%d")

def dateToStr(date: datetime.datetime) -> str:
    return date.strftime("%Y-%m-%d")

def createFId(cik: str, end: str, duration: Enum) -> str:
    '''
    Returns a Fiscal ID: cik, end, and Duration, connected by underscores.

    For example: 0000034088_2023-06-30_OneQuarter
    '''
    return "_".join([cik, end, duration.name])

def deconstructFId(fId: str) -> tuple[str, str, str]:
    '''
    Returns cik, end, Duration
    '''
    return fId.split('_')

def getLongShortOneQuarterFIds(ff: FiscalFinancial) -> tuple[str, str]:
    '''
    Returns long-duration fId and short-duration fId.

    The long-duration fId ends on the same date as the given FiscalFinancial. The short-duration 
    fId ends one quarter before. This function should not be used with FY or Q1 fiscal periods, and 
    will raise an error.
    '''
    cik, longEnd, _ = deconstructFId(ff.fId)
    if ff.fp == 'Q4':
        longDuration = concepts.Duration.Year
        shortDuration = concepts.Duration.ThreeQuarters
    elif ff.fp == 'Q3':
        longDuration = concepts.Duration.ThreeQuarters
        shortDuration = concepts.Duration.TwoQuarters
    elif ff.fp == 'Q2':
        longDuration = concepts.Duration.TwoQuarters
        shortDuration = concepts.Duration.OneQuarter
    else:
        raise Exception(f"Cannot get long- and short-duration Fiscal IDs of {ff.fp} fiscal period.")
    longId = createFId(cik, longEnd, longDuration)
    shortEnd = dateToStr(strToDate(ff.start) - datetime.timedelta(days=1))
    shortId = createFId(cik, shortEnd, shortDuration)
    return longId, shortId

def createFIdToFiscalFinancial(data: dict, cik: str) -> dict[str, dict] | None:
    '''
    Returns a dictionary mapping Fiscal ID to a FiscalFinancial with empty values, or None if the 
    dictionary cannot be created.

    In addition to the company-reported entries for FY with full year duration, Q3 with three 
    quarter duration, Q2 with two quarter duration, and Q1 with one quarter duration, this function 
    also creates one-quarter duration entries for Q4, Q3, and Q2. 
    '''
    if 'facts' not in data:
        print(f'{cik}: facts NOT FOUND')
        return None
    if 'us-gaap' not in data['facts']:
        print(f'{cik}: us-gaap NOT FOUND')
        return None
    # if 'Assets' not in data['facts']['us-gaap']:
    #     print(f'{cik}: Assets not found')
    #     return None
    if 'NetIncomeLoss' not in data['facts']['us-gaap']:
        print(f'{cik}: NetIncomeLoss not found')
        return None

    accnToEntry = {}
    # for entry in data['facts']['us-gaap']['Assets']['units']['USD']:
    for entry in data['facts']['us-gaap']['NetIncomeLoss']['units']['USD']:
        form = entry['form']
        if form == '10-K' or form == '10-Q':
            accn = entry['accn']
            # Use the most recent entry for each accn
            if (accn not in accnToEntry) or (entry['end'] > accnToEntry[accn]['end']):
                accnToEntry[accn] = entry

    fIdToFiscalFinancial = {}
    ends = []
    for accn, entry in accnToEntry.items():
        start = entry['start'] if 'start' in entry else None
        end = entry['end']
        form = entry['form']
        duration = getDuration(start, end, form)
        accn = entry['accn']
        fId = createFId(cik, end, duration)
        fiscalYear = entry['fy']
        fiscalPeriod = entry['fp']
        fIdToFiscalFinancial[fId] = FiscalFinancial(cik, fId, duration, start, end, accn, form, fiscalYear, fiscalPeriod)
        ends.append(end)
    
    # Add the missing one-quarter duration items
    ends.sort()
    fIds = [fId for fId in fIdToFiscalFinancial.keys()]
    for fId in fIds:
        ff = fIdToFiscalFinancial[fId]
        if ff.duration == concepts.Duration.Year or ff.duration == concepts.Duration.ThreeQuarters or ff.duration == concepts.Duration.TwoQuarters:
            i = ends.index(ff.end)
            if i == 0:
                continue
            priorQuarterEnd = strToDate(ends[i-1])
            startDate = priorQuarterEnd + datetime.timedelta(days=1)
            start = dateToStr(startDate)
            duration = concepts.Duration.OneQuarter
            quarterId = createFId(ff.cik, ff.end, duration)
            if ff.duration == concepts.Duration.Year:
                fiscalPeriod = 'Q4'
            elif ff.duration == concepts.Duration.ThreeQuarters:
                fiscalPeriod = 'Q3'
            else:
                fiscalPeriod = 'Q2'
            fIdToFiscalFinancial[quarterId] = FiscalFinancial(cik=cik, fId=quarterId, 
                                                              duration=duration, start=start, 
                                                              end=ff.end, accn=None, form=None, 
                                                              fy=ff.fy, fp=fiscalPeriod)
    return fIdToFiscalFinancial

def getConcepts(cik: str, data: dict, fIdToFiscalFinancial: dict) -> None:
    gaapData = data['facts']['us-gaap']
    for alias in gaapData.keys():
        if alias in concepts.aliasToConcept:
            entries = gaapData[alias]['units']['USD']
            for entry in entries:
                end = entry['end']
                fiscalPeriod = entry['fp']
                start = entry['start'] if 'start' in entry else None
                duration = getDuration(start, end, fiscalPeriod)
                entryId = createFId(cik, end, duration)
                if entryId in fIdToFiscalFinancial:
                    concept = concepts.aliasToConcept[alias].name
                    value = entry['val']
                    existingValues = fIdToFiscalFinancial[entryId].values[concept]
                    filingFy = entry['fy']
                    myFV = FiscalValue(concept, alias, value, filingFy)
                    addFiscalValues(existingValues, myFV)
    addMissingOneQuarterConcepts(fIdToFiscalFinancial)
    handleConceptIssues(fIdToFiscalFinancial)

def addFiscalValues(existing: list[FiscalValue], mine: FiscalValue) -> None:
    '''
    Determines whether and how a FiscalValue should be added to a list, then adds it if necessary.
    '''
    # If the list is empty, append it
    if not existing:
        existing.append(mine)
        return

    # If your value is the same as an existing one, do nothing
    for i in range(len(existing)):
        if existing[i].value == mine.value:
            return

    # If your new value is "better" than an existing value, replace the existing
    for i in range(len(existing)):
        if replaceFiscalValue(existing[i], mine):
            existing[i] = mine

    return

def replaceFiscalValue(A: FiscalValue, B: FiscalValue) -> bool:
    '''
    Returns True if FiscalValue A should be replaced by B. 
    
    A should be replaced by B if B is more recent (or at least not None).
    '''
    if B.filingFy and (not A.filingFy or B.filingFy > A.filingFy):
        return True

    return False


def addMissingOneQuarterConcepts(fIdToFiscalFinancial: dict) -> None:
    '''
    Add missing one-quarter-duration concepts. 

    For example, all fourth quarter concepts will be missing since they are not reported and must 
    be derived. Also, cash flow concepts will be missing for Q2 and Q3 since these are only 
    reported in two- and three-quarter durations. 
    '''
    for fId, ff in fIdToFiscalFinancial.items():
        if ff.duration == concepts.Duration.OneQuarter and ff.fp != 'Q1':
            for concept in concepts.Concepts:
                concept = concept.name
                values = ff.values[concept]
                if not values:
                    value = getOneQuarterValue(fIdToFiscalFinancial, ff, concept)
                    if value != None:
                        values.append(value)

def getOneQuarterValue(fIdToFf: dict[str, FiscalFinancial], ff: FiscalFinancial, concept: str) -> FiscalValue | None:
    longId, shortId = getLongShortOneQuarterFIds(ff)
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

def handleConceptIssues(fIdToFiscalFinancial: dict) -> None:
    ciks = set()
    msgCount = 0
    for fId, ff in fIdToFiscalFinancial.items():
        values = ff.values
        for c in concepts.Concepts:
            concept = c.name
            data = values[concept]
            if len(data) != 1:
                print(f'\nFID: {fId}, concept: {concept}, accn: {ff.accn}, Msg: {len(data)} values found => {data}')
                ciks.add(ff.cik)
                msgCount += 1
            # if len(data) == 1:
            #     print(f'ID {fId}: One value found: {data}')
    print(f'\n{msgCount} messages')
    for cik in ciks:
        fname = f'CIK{cik}.json'
        extractZipFileToJson(fname)

def getDuration(startDate: str | None, endDate: str, fiscalPeriod: str) -> Enum:
    if not startDate:
        return concepts.Duration.OneQuarter
    start = strToDate(startDate)
    end = strToDate(endDate)
    duration = (end - start).days
    if 80 < duration < 100:
        return concepts.Duration.OneQuarter
    if 170 < duration < 190:
        return concepts.Duration.TwoQuarters
    if 260 < duration < 280:
        return concepts.Duration.ThreeQuarters
    if 330 < duration < 380:
        return concepts.Duration.Year
    return concepts.Duration.Other

def extractZipFileToJson(filename: str):
    # filename = "CIK0000320193.json" # Apple
    with zipfile.ZipFile(config.ZIP_PATH, 'r') as zf:
        with zf.open(filename) as inFile:
            content = inFile.read()
            data = json.loads(content.decode('utf-8'))
            with open(os.path.join(config.DATA_DIR, filename), 'w') as outFile:
                json.dump(data, outFile, indent=2)

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
    cnx = mysql.connector.connect(host=config.MYSQL_HOST, database=config.MYSQL_DATABASE, user=os.getenv("MYSQL_USER"), password=os.getenv("MYSQL_PASSWORD"))
    cursor = cnx.cursor()
    query = ("SELECT CIK FROM companies;")
    cursor.execute(query)
    cursor.fetchall() # Need to "use up" cursor
    # for cik in [('0000320193',)]: # Apple
    for cik in [('0000320193',), ('0000004962',)]: # Apple, American Express
    # for cik in cursor:
        cik = cik[0]
        print(f'\nCIK: {cik}')
        fname = 'CIK' + cik + '.json'
        with zipfile.ZipFile(config.ZIP_PATH, 'r') as z:
            with open("test.txt", 'w') as write_file:
                try:
                    with z.open(fname) as f:
                        content = f.read()
                        data = json.loads(content.decode('utf-8'))
                        fIdToFiscalFinancial = createFIdToFiscalFinancial(data, cik)
                        if fIdToFiscalFinancial:
                            getConcepts(cik, data, fIdToFiscalFinancial)
                except KeyError as e:
                    print(f'KeyError: {e}')

    cnx.commit()
    cursor.close()
    cnx.close()

if __name__ == "__main__":
    run()