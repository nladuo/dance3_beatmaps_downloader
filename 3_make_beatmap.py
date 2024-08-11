import requests
import json
import pymongo

client = pymongo.MongoClient()
db = client.dance3
coll = db.songs

count = 0
for it in coll.find({}):
    count += 1
    print(count, it["GoodsInfo"]["GoodsName"], it["GoodsInfo"]["LevelList"])
    levelMap = {}
    for level in it["GoodsInfo"]["LevelList"]:
        if level["MusicLev"] >= 0:
            print(level)
            levelMap[level["MusicLevNew"]] = level

    beatmaps = []
    for file in it["GoodsInfo"]["ListFile"]:
        if file["FileType"] == 1:
            print(file)
            try:
                file["Level"] = levelMap[file["MusicLev"]]["MusicLevel"]
                file["Lev"] = levelMap[file["MusicLev"]]["MusicLev"]
                beatmaps.append(file)
            except:pass

    coll.update({"_id": it["_id"]}, {
        "$set": {
            "BeatMaps": beatmaps
        }
    })
