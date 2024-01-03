import requests
import pprint

url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK0001637207.json'
headers = {'user-agent': 'jsripraj@gmail.com'}
r = requests.get(url, headers=headers)
# print(f'status {r.status_code}')
# print(r.text)
with open('out.txt', 'w') as f:
    f.write(pprint.pformat(r.json(), width=160))
# print(r.json())