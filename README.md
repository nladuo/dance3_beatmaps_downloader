# dance3_beatmaps_downloader

舞立方（Dance3）谱面下载器，输出格式：Malody (.mc)。

改造说明：原仓库使用本地 MongoDB（pymongo）存储，现改为 **SQLite 单文件
`dance3.sqlite3`**（无需额外服务），并用 `info_done / beatmaps_done /
downloaded` 三个标记支持各步骤断点续跑。同时跳过数据源标记为
`IsBad=True` 的损坏谱面/音频（如 322-出山DJ 的坏 mp3）。

## 依赖

```shell
pip install requests
```

## 使用

### 1. 下载谱面列表（全量歌曲，写入 sqlite）
```shell
python 1_crawl_info_list.py
```

### 2. 下载谱面详情（GoodsInfo，含 ListFile / LevelList）
```shell
python 2_crawl_info_detail.py
```

### 3. 构建谱面列表 BeatMaps（提取 FileType=1，跳过 IsBad）
```shell
python 3_make_beatmap.py
```

### 4. 下载谱面（音频 + 谱面文本转 .mc）→ `beatmaps/{GoodsID}-{GoodsName}/`
```shell
mkdir beatmaps
python 4_download_beatmaps.py
```

### 其他
```shell
# 导出所有歌曲信息 → info_data.json（{GoodsID: record}）
python dumps_infos.py
```

## 数据字段说明

- 列表接口 `GetGoodsMusic`：歌曲 `MusicID / GoodsID / GoodsName / AudioUrl / OwnerName` 等。
- 详情接口 `GetGoodsInfo`：`GoodsInfo.BeginSeconds / BPM / LevelList / ListFile`。
- `ListFile` 中 `FileType=1` 为谱面文本、`FileType=2` 为音频；`IsBad=True` 表示损坏文件，会被跳过。
- 谱面难度：`ListFile.MusicLev` 对应 `LevelList` 中 `MusicLevNew` 的条目，其 `MusicLevel` 即为
  谱面显示等级（.mc 的 `meta.version` 形如 `歌曲名-等级`，如 `New World in the Dream-12`）。
