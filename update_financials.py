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
    def __init__(self, concept: str, alias: str, value: str):
        self.concept = concept
        self.alias = alias
        self.value = value

    def __repr__(self):
        return f"FiscalValue('{self.concept}', '{self.alias}', '{self.value}')"

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

def createFId(accn: str, end: str, duration: Enum) -> str:
    '''
    Returns a Fiscal ID: <accn>_<end date yyyy-mm-dd>_<duration (see concepts.py)>
    '''
    return "_".join([accn, end, duration.name])

def deconstructFId(fId: str) -> tuple[str, str, str]:
    return fId.split('_')

def createFIdToData(data: dict, cik: str) -> dict[str, dict] | None:
    '''
    Returns dict mapping ID to data dict. 
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
        period = getDuration(start, end, form)
        accn = entry['accn']
        fId = createFId(accn, end, period)
        fiscalYear = entry['fy']
        fiscalPeriod = entry['fp']
        fIdToFiscalFinancial[fId] = FiscalFinancial(cik, fId, period, start, end, accn, form, fiscalYear, fiscalPeriod)
        ends.append(end)
    
    # Add the missing Q4s
    ends.sort()
    fIds = [fId for fId in fIdToFiscalFinancial.keys()]
    for fId in fIds:
        ff = fIdToFiscalFinancial[fId]
        if ff.period == concepts.Duration.Year:
            i = ends.index(ff.end)
            if i == 0:
                continue
            priorQuarterEnd = strToDate(ends[i-1])
            startDate = priorQuarterEnd + datetime.timedelta(days=1)
            start = dateToStr(startDate)
            duration = concepts.Duration.OneQuarter
            quarterId = createFId(ff.accn, ff.end, duration)
            fIdToFiscalFinancial[quarterId] = FiscalFinancial(cik, quarterId, duration, start, ff.end, ff.accn, None, None, None)
    return fIdToFiscalFinancial

def getConcepts(data: dict, fIdToFiscalFinancial: dict) -> None:
    gaapData = data['facts']['us-gaap']
    for alias in gaapData.keys():
        if alias in concepts.aliasToConcept:
            entries = gaapData[alias]['units']['USD']
            for entry in entries:
                accn = entry['accn']
                end = entry['end']
                form = entry['form']
                start = entry['start'] if 'start' in entry else None
                period = getDuration(start, end, form)
                entryId = createFId(accn, end, period)
                if entryId in fIdToFiscalFinancial:
                    concept = concepts.aliasToConcept[alias].name
                    value = entry['val']
                    fIdToFiscalFinancial[entryId].values[concept].append(FiscalValue(concept, alias, value))
    getMissingOneQuarterConcepts(fIdToFiscalFinancial)
    handleConceptIssues(fIdToFiscalFinancial)

def getMissingOneQuarterConcepts(fIdToFiscalFinancial: dict) -> None:
    for fId, ff in fIdToFiscalFinancial.items():
        if fId.endswith(concepts.Duration.OneQuarter.name):
            # find the concepts that OneQuarter is missing, should be cash flow concepts
            for concept in concepts.Concepts:
                concept = concept.name
                data = ff.values[concept]
                if not data:
                    elif ff.fp == 'Q2':
                        # get id of twoquarter
                        threeQuarterId = idSub + concepts.Duration.ThreeQuarters.name
                        twoQuarterId = idSub + concepts.Duration.ThreeQuarters.name
                        threeQuarterId = idSub + concepts.Duration.ThreeQuarters.name

                    # try to calculate as TwoQuarter minus OneQuarter
                    # get id of twoquarter w same end date
                    # get onequarter end date
                    # get id of onequarter

def getOneQuarterValue(ff: FiscalFinancial):
    if ff.fp == 'Q3':
        # try to calculate as ThreeQuarter minus TwoQuarter
        # get id of threequarter w same end date
        # get accn from fId
        # get date from fId
        accn, q3End, _ = deconstructFId(fId)
        # use ThreeQuarter
        q3Id = createFId(accn, q3End, concepts.Duration.ThreeQuarters)
        # get twoquarter end date
        q2End = strToDate(ff.start) - datetime.timedelta(days=1)
        q2Id = createFId(accn, q2End, concepts.Duration.TwoQuarters)
        q3Value = fIdToFiscalFinancial[q3Id].values[concept][0].value
        q2Value = fIdToFiscalFinancial[q2Id].values[concept][0].value
        data.append(q3Value - q2Value)


def handleConceptIssues(fIdToFiscalFinancial: dict) -> None:
    ciks = set()
    for fId, ff in fIdToFiscalFinancial.items():
        values = ff.values
        for c in concepts.Concepts:
            concept = c.name
            data = values[concept]
            if len(data) != 1:
                print(f'CIK: {ff.cik}, FID: {fId}, Concept: {concept}, Msg: {len(data)} values found => {data}')
                ciks.add(ff.cik)
            # if len(data) == 1:
            #     print(f'ID {fId}: One value found: {data}')
    for cik in ciks:
        fname = f'CIK{cik}.json'
        extractZipFileToJson(fname)

def getDuration(startDate: str | None, endDate: str, form: str) -> Enum:
    if not startDate:
        return concepts.Duration.OneQuarter if form == "10-Q" else concepts.Duration.Year
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
    # cursor.fetchall()
    # for cik in ['0000320193', '0002011641']: # Apple, Ferguson Enterprises
    for cik in cursor:
        cik = cik[0]
        print(f'\nCIK: {cik}')
        fname = 'CIK' + cik + '.json'
        with zipfile.ZipFile(config.ZIP_PATH, 'r') as z:
            with open("test.txt", 'w') as write_file:
                try:
                    with z.open(fname) as f:
                        content = f.read()
                        data = json.loads(content.decode('utf-8'))
                        fIdToData = createFIdToData(data, cik)
                        if fIdToData:
                            getConcepts(data, fIdToData)
                except KeyError as e:
                    print(f'KeyError: {e}')

    cnx.commit()
    cursor.close()
    cnx.close()

if __name__ == "__main__":
    run()