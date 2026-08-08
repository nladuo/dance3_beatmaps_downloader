# -*- coding: utf-8 -*-
"""1. 下载谱面列表 → sqlite（dance3.sqlite3）。"""
import argparse
import json

import requests

import db

API = "https://dancedemo.shenghuayule.com/Dance/api/Goods/GetGoodsMusic"
PARAMS = "page={page}&pagesize=200&tag=&language=&orderby=2&ordertype=2&keyword="


def main():
    parser = argparse.ArgumentParser(description="下载舞立方谱面列表写入 sqlite")
    parser.add_argument("--limit_pages", type=int, default=0, help="只抓前 N 页（0=全部，用于测试）")
    args = parser.parse_args()

    conn = db.get_conn()
    data = json.loads(
        requests.get(API + "?" + PARAMS.format(page=1), timeout=30).content.decode("utf8")
    )
    record_count = int(data["RecordCount"])
    total_page = int(record_count / 200 + 1)
    if args.limit_pages:
        total_page = min(total_page, args.limit_pages)
    print(f"RecordCount={record_count}, pages to crawl={total_page}")

    new_count = 0
    for i in range(total_page):
        resp = requests.get(API + "?" + PARAMS.format(page=i + 1), timeout=30)
        page_data = json.loads(resp.content.decode("utf8"))
        for it in page_data["List"]:
            if db.upsert_song(conn, it):
                new_count += 1
                print("new:", it.get("MusicID"), it.get("GoodsName"))
        print(f"page {i + 1}/{total_page} done")
    print(f"done. total in db: {db.count(conn)}, new this run: {new_count}")


if __name__ == "__main__":
    main()
