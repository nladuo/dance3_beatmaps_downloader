import requests
import json
import pymongo

client = pymongo.MongoClient()
db = client.dance3
coll = db.songs


resp = requests.get(f"https://dancedemo.shenghuayule.com/Dance/api/Goods/GetGoodsMusic?page=1&pagesize=200&tag=&language=&orderby=2&ordertype=2&keyword=",
    headers={})
data = json.loads(resp.content.decode("utf8"))
record_count = data["RecordCount"]
total_page = int(record_count / 200 + 1)


for i in range(total_page):
    resp = requests.get(f"https://dancedemo.shenghuayule.com/Dance/api/Goods/GetGoodsMusic?page={i+1}&pagesize=200&tag=&language=&orderby=2&ordertype=2&keyword=",
             headers={})
    data = json.loads(resp.content.decode("utf8"))
    # print(data)
    for it in data["List"]:
        if coll.find({"MusicID": it["MusicID"]}).count() == 0:
            print(it)
            coll.insert(it)

