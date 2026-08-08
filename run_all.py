# -*- coding: utf-8 -*-
"""顺序执行 1-4 步全量爬取（后台运行用）。"""
import subprocess
import sys
import time

STEPS = [
    ("1_crawl_info_list.py", ["-u", "1_crawl_info_list.py"]),
    ("2_crawl_info_detail.py", ["-u", "2_crawl_info_detail.py"]),
    ("3_make_beatmap.py", ["-u", "3_make_beatmap.py"]),
    ("4_download_beatmaps.py", ["-u", "4_download_beatmaps.py"]),
]

def main():
    total = len(STEPS)
    for i, (name, argv) in enumerate(STEPS, 1):
        print(f"\n===== [{time.strftime('%Y-%m-%d %H:%M:%S')}] STEP {i}/{total}: {name} =====", flush=True)
        r = subprocess.run([sys.executable] + argv)
        if r.returncode != 0:
            print(f"!!!!! STEP FAILED: {name} rc={r.returncode}", flush=True)
            sys.exit(r.returncode)
    print(f"\n===== ALL DONE {time.strftime('%Y-%m-%d %H:%M:%S')} =====", flush=True)

if __name__ == "__main__":
    main()
