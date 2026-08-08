# -*- coding: utf-8 -*-
"""导出所有歌曲信息 → info_data.json（{GoodsID: record}），与原来 MongoDB 版本一致。"""
import json

import db


def main():
    conn = db.get_conn()
    info_data = db.dump_all(conn)
    with open("info_data.json", "w", encoding="utf-8") as f:
        json.dump(info_data, f, ensure_ascii=False, indent=1)
    print("dumped:", len(info_data))


if __name__ == "__main__":
    main()
