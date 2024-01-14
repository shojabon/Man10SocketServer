import time

import requests
import tqdm

url = 'http://localhost:4567/v1/server/scommand'
data = {
    "command": "mshop moneyGive ffa9b4cb-ada1-4597-ad24-10e318f994c8 1"
}
session = requests.Session()
start_time = time.time()
for x in tqdm.tqdm(range(10000)):
    response = session.post(url, data=data)

print("time: ", time.time() - start_time)

# url = 'http://localhost:4567/v1/server/exec'
# data = {
#     "command": "mshop moneyGive ffa9b4cb-ada1-4597-ad24-10e318f994c8 1"
# }
# session = requests.Session()
# start_time = time.time()
# for x in tqdm.tqdm(range(100)):
#     response = session.post(url, data=data)
#
# print("time: ", time.time() - start_time)