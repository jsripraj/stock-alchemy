import requests
import pprint
import json

OUTPUT_FILE = "out.txt"
url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK0001637207.json'
headers = {'user-agent': 'jsripraj@gmail.com'}

r = requests.get(url, headers=headers)
# print(f'status {r.status_code}')
# print(r.text)
with open(OUTPUT_FILE, 'w') as f:
    # f.write(pprint.pformat(r.json(), width=160))
    # output = str(r.json())
    # output.replace(r"'", r'"')
    json_output = json.dumps(r.json())
    f.write(json_output)
# print(r.json())
