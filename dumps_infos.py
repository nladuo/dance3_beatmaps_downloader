import json

import pymongo

info_data = {}

client = pymongo.MongoClient()
db = client.dance3
coll = db.songs


for song in coll.find({}):
    del song["_id"]
    print(song)
    info_data[song["GoodsID"]] = song

with open("info_data.json", "w") as f:
    json.dump(info_data, f)