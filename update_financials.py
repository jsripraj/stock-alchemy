import requests
import os
import config

headers = {'User-Agent': config.EMAIL}
response = requests.get(config.URL_SEC_COMPANYFACTS, headers=headers)