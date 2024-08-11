import requests
import json
import pymongo

client = pymongo.MongoClient()
db = client.dance3
coll = db.songs

count = 0
for it in coll.find({}):
    if (("GoodsInfo" in it) and ("GoodsID" not in it["GoodsInfo"])) or ("GoodsInfo" not in it):
        resp = requests.get(f"https://dancedemo.shenghuayule.com/Dance/api/MusicData/GetGoodsInfo?musicId={it['MusicID']}",
                 headers={
                 })
        data = json.loads(resp.content.decode("utf8"))
        count += 1
        print(count, data)
        coll.update({"_id": it["_id"]}, {
            "$set": {
                "GoodsInfo": data
            }
        })
