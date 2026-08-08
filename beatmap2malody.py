# -*- coding: utf-8 -*-
"""把舞立方谱面文本（如 "123-1 45-2..."）转成 Malody .mc JSON。

原仓库通过共享文件 test.txt 传递谱面文本，多曲下载时会互相覆盖；
这里改为直接传 chart_text 字符串，兼容不传（读取 test.txt）。
"""
import json
import time
from fractions import Fraction


def decimal_to_fraction(decimal):
    """将小数转换为分数并化简。"""
    fraction = Fraction(decimal).limit_denominator()
    return fraction.numerator, fraction.denominator


def get_beatmap_json(OwnerName, BPM, audio_file_name, BeginSeconds, GoodsName, lev, chart_text=None):
    offset = -int(float(BeginSeconds) * 1000)

    mc_data = {
        "meta": {
            "creator": OwnerName,
            "version": f"{GoodsName}-{lev}",
            "mode": 0,
            "time": int(time.time()),
            "song": {
                "title": GoodsName,
                "artist": "",
            },
            "mode_ext": {
                "column": 6
            }
        },
        "time": [
            {
                "beat": [0, 0, 1],
                "bpm": BPM
            },
        ],
        "extra": {
            "test": {
                "divide": 6,
                "speed": 100,
                "save": 0,
                "lock": 0,
                "edit_mode": 0
            }
        }
    }

    if chart_text is None:
        with open("test.txt", "r", encoding="utf-8") as f:
            chart_text = f.read()

    last_note = {
        "beat": [0, 0, 1],
        "sound": audio_file_name,
        "vol": 100,
        "offset": offset,
        "type": 1
    }
    notes = []

    for line in chart_text.split():
        ls = line.split("-")
        if len(ls) == 2:
            for ch in ls[0]:
                beat = int(float(ls[1]))
                decimal_ = float(ls[1]) - beat
                if decimal_ == 0:
                    numerator, denominator = 0, 1
                else:
                    numerator, denominator = decimal_to_fraction(decimal_)
                notes.append({
                    "column": int(ch) - 1,
                    "beat": [beat, numerator, denominator]
                })
        elif len(ls) == 3:
            for ch in ls[0]:
                beat = int(float(ls[1]))
                endbeat = int(float(ls[2]))
                decimal_ = float(ls[1]) - beat
                if decimal_ == 0:
                    numerator, denominator = 0, 1
                else:
                    numerator, denominator = decimal_to_fraction(decimal_)
                decimal_2 = float(ls[2]) - endbeat
                if decimal_2 == 0:
                    numerator2, denominator2 = 0, 1
                else:
                    numerator2, denominator2 = decimal_to_fraction(decimal_2)
                notes.append({
                    "column": int(ch) - 1,
                    "beat": [beat, numerator, denominator],
                    "endbeat": [endbeat, numerator2, denominator2]
                })

    notes.append(last_note)
    mc_data["note"] = notes

    return mc_data
