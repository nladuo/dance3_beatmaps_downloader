# -*- coding: utf-8 -*-
"""3. 构建谱面列表 BeatMaps（从 GoodsInfo.ListFile 提取 FileType=1）→ 更新 sqlite。

- 跳过 IsBad=True 的谱面文件：数据源对坏文件有 IsBad 标记（如 322-出山DJ 的坏 mp3/谱面）。
- 歌曲标签 TagList（如 乱黄、散点、高难度）会同步到 rec["Tags"] 和每张谱面 BeatMaps[i]["Tags"]。
- 只处理 beatmaps_done=0 的记录，支持断点续跑。
"""
import argparse

import db


def main():
    parser = argparse.ArgumentParser(description="构建 BeatMaps 写入 sqlite")
    parser.add_argument("--limit", type=int, default=0, help="只处理前 N 首（0=全部，用于测试）")
    args = parser.parse_args()

    conn = db.get_conn()
    count = 0
    skipped = 0
    for music_id, rec in db.iter_pending(conn, "beatmaps_done"):
        if args.limit and count >= args.limit:
            break
        info = rec.get("GoodsInfo") or {}
        tags = rec.get("TagList") or []

        # MusicLev >= 0 的 LevelList 项才是真实谱面难度（MusicLevNew -> 难度条目）
        level_map = {}
        for level in info.get("LevelList", []):
            if level.get("MusicLev", -1) >= 0:
                level_map[level["MusicLevNew"]] = level

        beatmaps = []
        for f in info.get("ListFile", []):
            if f.get("FileType") != 1:
                continue
            if f.get("IsBad"):
                skipped += 1
                print("skip bad chart:", music_id, f.get("Url"))
                continue
            lv = level_map.get(f.get("MusicLev"))
            if not lv:
                print("no level for chart:", music_id, "MusicLev=", f.get("MusicLev"))
                continue
            f["Level"] = lv["MusicLevel"]   # 谱面显示等级（如 11/12/13）
            f["Lev"] = lv["MusicLev"]
            f["Tags"] = tags                 # 谱面标签（来自歌曲 TagList）
            beatmaps.append(f)

        rec["BeatMaps"] = beatmaps
        rec["Tags"] = tags
        db.save(conn, music_id, rec, beatmaps_done=True)
        count += 1
        print(count, rec.get("GoodsName"), [b.get("MusicLev") for b in beatmaps], tags)

    print(f"done. processed={count}, skipped_bad_charts={skipped}")


if __name__ == "__main__":
    main()
