import json
import os
import requests
import pymongo
from beatmap2malody import get_beatmap_json

client = pymongo.MongoClient()
db = client.dance3
coll = db.songs

count = 0
its = []
for it in coll.find({}):
    del it["_id"]
    # print(it)
    its.append(it)
    GoodsID = it["GoodsID"]
    GoodsName = it["GoodsName"]
    AudioUrl = it["AudioUrl"]
    BeatMaps = it["BeatMaps"]
    # print(GoodsID, GoodsName)
    filepath = f"{GoodsID}-{GoodsName}".replace("/", "|")
    if not os.path.exists(f"beatmaps/{filepath}"):
        os.mkdir(f"beatmaps/{filepath}")
        audio_file_name = AudioUrl.split("/")[-1]
        count += 1
        print(count, audio_file_name, AudioUrl, BeatMaps)

        OwnerName = it["OwnerName"]
        BeginSeconds = it["GoodsInfo"]["BeginSeconds"]
        BPM = it["GoodsInfo"]["BPM"]
        with open(f"beatmaps/{filepath}/{audio_file_name}", "wb") as f2:
            f2.write(requests.get(AudioUrl).content)

        for beatmap in BeatMaps:
            try:
                # print(beatmap["Url"])
                # print(beatmap["Level"])
                lev = beatmap["Level"]
                with open("test.txt", "wb") as f2:
                    f2.write(requests.get(beatmap["Url"]).content)
                mc_filename = beatmap["Url"].split("/")[-1].split(".")[0] + ".mc"

                mc_json = get_beatmap_json(OwnerName, BPM, audio_file_name, BeginSeconds, GoodsName, lev)

                with open(f"beatmaps/{filepath}/{mc_filename}", "w") as f2:
                    json.dump(mc_json, f2)
            except:
                pass



