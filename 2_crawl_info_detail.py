# -*- coding: utf-8 -*-
"""2. 下载谱面详情（GoodsInfo）→ 更新 sqlite。"""
import argparse
import json
import time

import requests

import db

API = "https://dancedemo.shenghuayule.com/Dance/api/MusicData/GetGoodsInfo?musicId={mid}"


def main():
    parser = argparse.ArgumentParser(description="下载谱面详情写入 sqlite")
    parser.add_argument("--limit", type=int, default=0, help="只处理前 N 首（0=全部，用于测试）")
    parser.add_argument("--sleep", type=float, default=0.2, help="每首之间的间隔秒数")
    args = parser.parse_args()

    conn = db.get_conn()
    count = 0
    for music_id, rec in db.iter_pending(conn, "info_done"):
        if args.limit and count >= args.limit:
            break
        try:
            data = json.loads(
                requests.get(API.format(mid=music_id), timeout=30).content.decode("utf8")
            )
        except Exception as e:
            print("ERR", music_id, e)
            continue
        rec["GoodsInfo"] = data
        db.save(conn, music_id, rec, info_done=True)
        count += 1
        print(count, data.get("GoodsName"), data.get("LevelList"))
        time.sleep(args.sleep)
    print("done. updated:", count)


if __name__ == "__main__":
    main()
