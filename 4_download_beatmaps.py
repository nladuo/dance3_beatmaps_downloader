# -*- coding: utf-8 -*-
"""4. 下载谱面：音频 mp3 + 谱面文本转 .mc → beatmaps/{GoodsID}-{GoodsName}/。

- 跳过音频 IsBad=True 的歌曲（数据源坏音频标记，如 322-出山DJ 的 mp3）。
- 文件名做 Windows 非法字符清洗，避免目录名乱码/非法。
- 只处理 downloaded=0 的记录，支持断点续跑（已存在文件不重复下载）。
- 网络请求带重试；单首失败不中断整体（失败列表打印在结尾）。
"""
import argparse
import json
import os
import re
import time

import requests

import db
from beatmap2malody import get_beatmap_json

BASE_DIR = "beatmaps"
HEADERS = {"User-Agent": "Mozilla/5.0"}

_ILLEGAL = re.compile(r"[\\/:*?\"<>|\x00-\x1f]")
_WIN_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}


def sanitize_name(name):
    """清洗为 Windows 合法目录名：非法字符->_，处理保留名/尾点空格/超长。"""
    name = (name or "").strip()
    name = _ILLEGAL.sub("_", name)
    name = name.rstrip(". ")
    if not name:
        return "_"
    if name.split(".")[0].upper() in _WIN_RESERVED:
        name = "_" + name
    if len(name) > 200:
        name = name[:200].rstrip(". ")
    return name or "_"


def is_audio_bad(rec):
    for f in (rec.get("GoodsInfo") or {}).get("ListFile", []):
        if f.get("FileType") == 2 and f.get("IsBad"):
            return True
    return False


def get_with_retry(url, timeout=60, tries=3):
    """GET 带重试（网络抖动/5xx 兜底），失败抛出最后一次异常。"""
    last = None
    for i in range(tries):
        try:
            return requests.get(url, timeout=timeout, headers=HEADERS)
        except Exception as e:
            last = e
            print("retry", i + 1, url, repr(e))
            time.sleep(2 * (i + 1))
    raise last


def main():
    parser = argparse.ArgumentParser(description="下载音频与谱面 .mc")
    parser.add_argument("--limit", type=int, default=0, help="只处理前 N 首（0=全部，用于测试）")
    parser.add_argument("--out", type=str, default=BASE_DIR, help="输出目录（默认 beatmaps）")
    args = parser.parse_args()

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)
    conn = db.get_conn()
    count = 0
    failed = []
    for music_id, rec in db.iter_pending(conn, "downloaded"):
        if args.limit and count >= args.limit:
            break
        goods_id = rec.get("GoodsID")
        goods_name = rec.get("GoodsName") or ""
        audio_url = rec.get("AudioUrl")
        beatmaps = rec.get("BeatMaps") or []

        if not goods_id or not beatmaps:
            # 无谱面（或全部损坏）的歌曲直接标记完成，避免重复处理
            db.save(conn, music_id, rec, downloaded=True)
            continue
        if is_audio_bad(rec):
            print("skip bad audio:", music_id, goods_name, audio_url)
            db.save(conn, music_id, rec, downloaded=True)
            continue

        try:
            folder = os.path.join(out_dir, f"{goods_id}-{sanitize_name(goods_name)}")
            os.makedirs(folder, exist_ok=True)

            audio_file_name = audio_url.split("/")[-1] if audio_url else ""
            audio_path = os.path.join(folder, audio_file_name) if audio_file_name else None
            if audio_path and not os.path.exists(audio_path):
                print("download audio:", audio_file_name)
                resp = get_with_retry(audio_url, timeout=120)
                resp.raise_for_status()
                with open(audio_path, "wb") as f2:
                    f2.write(resp.content)

            info = rec.get("GoodsInfo") or {}
            owner_name = rec.get("OwnerName", "")
            begin_seconds = info.get("BeginSeconds", 0)
            bpm = info.get("BPM", 120)

            for beatmap in beatmaps:
                try:
                    lev = beatmap["Level"]
                    url = beatmap["Url"]
                    resp = get_with_retry(url, timeout=60)
                    resp.raise_for_status()
                    chart_text = resp.content.decode("utf8", errors="replace")
                    mc_name = url.split("/")[-1].split(".")[0] + ".mc"
                    mc_json = get_beatmap_json(
                        owner_name, bpm, audio_file_name, begin_seconds, goods_name, lev, chart_text
                    )
                    with open(os.path.join(folder, mc_name), "w", encoding="utf-8") as f2:
                        json.dump(mc_json, f2, ensure_ascii=False)
                    print("chart:", mc_name, "lev:", lev)
                except Exception as e:
                    print("ERR chart", music_id, beatmap.get("Url"), repr(e))

            db.save(conn, music_id, rec, downloaded=True)
            count += 1
            print(count, goods_id, goods_name, "done")
        except Exception as e:
            failed.append(music_id)
            print("FAIL song", music_id, goods_name, repr(e))

    print("done. downloaded:", count, "failed:", len(failed), failed[:20])


if __name__ == "__main__":
    main()
