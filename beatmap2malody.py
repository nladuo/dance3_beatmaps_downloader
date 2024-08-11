import json
import time
from fractions import Fraction


def decimal_to_fraction(decimal):
    """
    将小数转换为分数并化简

    参数：
    decimal (float): 要转换的小数

    返回值：
    tuple: 包含分子和分母的元组
    """
    # 将小数转换为分数
    fraction = Fraction(decimal).limit_denominator()

    # 获取分子和分母
    numerator = fraction.numerator
    denominator = fraction.denominator

    return numerator, denominator


def get_beatmap_json(OwnerName, BPM, audio_file_name, BeginSeconds, GoodsName, lev):
    # BPM = 134.0
    # BeginSeconds = int(2.2 * 1000)
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

    last_note = {
        "beat": [0, 0, 1],
        "sound": audio_file_name,
        "vol": 100,
        "offset": offset,
        "type": 1
    }
    notes = []

    with open("test.txt", "r") as f:
        for line in f.read().split():
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
    print(mc_data)

    return mc_data

