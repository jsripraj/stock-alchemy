import requests
import os
import zipfile
import json
from pprint import pp
import mysql.connector
from collections import defaultdict
from datetime import datetime
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
    def __init__(self, cik: str, fId: str, periodType: Enum, end: str, accn: str, form: str, fy: str , fp: str):
        self.cik: str = cik
        self.fId: str = fId # fiscal ID
        self.periodType: Enum = periodType
        self.end: str = end
        self.accn: str = accn # Accession number
        self.form: str = form
        self.fy: str = fy
        self.fp: str = fp
        self.values: dict[str, list[FiscalValue]] = defaultdict(list)

def createFId(accn: str, end: str, periodType: Enum) -> str:
    return "_".join([accn, end, periodType.name])

def createFIdToData(data: dict, cik: str) -> dict[str, dict] | None:
    '''
    Returns dict mapping ID to data dict. 
    '''
    if 'facts' not in data:
        print(f'{fname}: facts NOT FOUND')
        return None
    if 'us-gaap' not in data['facts']:
        print(f'{fname}: us-gaap NOT FOUND')
        return None
    if 'Assets' not in data['facts']['us-gaap']:
        print(f'{fname}: Assets not found')
        return None

    accnToEntry = {}
    for entry in data['facts']['us-gaap']['Assets']['units']['USD']:
        form = entry['form']
        if form == '10-K' or form == '10-Q':
            accn = entry['accn']
            if (accn not in accnToEntry) or (entry['end'] > accnToEntry[accn]['end']):
                accnToEntry[accn] = entry

    fIdToFiscalFinancial = {}
    for accn, entry in accnToEntry.items():
        start = entry['start'] if 'start' in entry else None
        end = entry['end']
        form = entry['form']
        period = getPeriodType(start, end, form)
        accn = entry['accn']
        fId = createFId(accn, end, period)
        fiscalYear = entry['fy']
        fiscalPeriod = entry['fp']
        fIdToFiscalFinancial[fId] = FiscalFinancial(cik, fId, period, end, accn, form, fiscalYear, fiscalPeriod)
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
                period = getPeriodType(start, end, form)
                entryId = createFId(accn, end, period)
                if entryId in fIdToFiscalFinancial:
                    concept = concepts.aliasToConcept[alias].name
                    value = entry['val']
                    fIdToFiscalFinancial[entryId].values[concept].append(FiscalValue(concept, alias, value))

    for fId, ff in fIdToFiscalFinancial.items():
        for concept in concepts.Concepts:
            values = ff.values[concept.name]
            if not values:
                print(f'ID {fId}: No values found')
            elif len(values) > 1:
                print(f'ID {fId}: Too many values found: {values}')
            else:
                print(f'ID {fId}: One value found: {values[0]}')

def getPeriodType(startDate: str | None, endDate: str, form: str) -> Enum:
    if not startDate:
        return concepts.PeriodType.Quarter if form == "10-Q" else concepts.PeriodType.Year
    start = datetime.strptime(startDate, "%Y-%m-%d")
    end = datetime.strptime(endDate, "%Y-%m-%d")
    days = (end - start).days
    if 80 < days < 100:
        return concepts.PeriodType.Quarter
    if 330 < days < 380:
        return concepts.PeriodType.Year
    return concepts.PeriodType.Other

# Download companyfacts.zip
# headers = {'User-Agent': config.EMAIL}
# with requests.get(config.URL_SEC_COMPANYFACTS, headers=headers, stream=True) as r:
#     r.raise_for_status()
#     os.makedirs(os.path.dirname(config.ZIP_PATH), exist_ok=True)
#     with open(config.ZIP_PATH, "wb") as f:
#         for chunk in r.iter_content(chunk_size=config.CHUNK_SIZE):
#             if chunk:
#                 f.write(chunk)

cnx = mysql.connector.connect(host=config.MYSQL_HOST, database=config.MYSQL_DATABASE, user=os.getenv("MYSQL_USER"), password=os.getenv("MYSQL_PASSWORD"))
cursor = cnx.cursor()
query = ("SELECT CIK FROM companies")
cursor.execute(query)
cursor.fetchall()
# for cik in cursor:
#     cik = cik[0]
for cik in ['0000320193', '0002011641']: # Apple, Ferguson Enterprises
    fname = 'CIK' + cik + '.json'
    with zipfile.ZipFile(config.ZIP_PATH, 'r') as z:
        with open("test.txt", 'w') as write_file:
            try:
                with z.open(fname) as f:
                    content = f.read()
                    data = json.loads(content.decode('utf-8'))
                    fIdToData = createFIdToData(data, cik)
                    if fIdToData:
                        print(f'\nCIK: {cik}')
                        getConcepts(data, fIdToData)
            except KeyError as e:
                print(f'KeyError: {e}')

cnx.commit()
cursor.close()
cnx.close()

# fname = "CIK0000320193.json" # Apple
# with zipfile.ZipFile(config.ZIP_PATH, 'r') as z:
#     with z.open(fname) as f:
#         content = f.read()
#         data = json.loads(content.decode('utf-8'))
#         with open("apple.json", 'w') as write_file:
#             json.dump(data, write_file, indent=2)