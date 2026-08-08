# -*- coding: utf-8 -*-
"""舞立方谱面列表 Web 界面（纯 Python 标准库，无需额外依赖）。

用法：
    python webui.py [--port 8080] [--db dance3.sqlite3] [--host 127.0.0.1]

打开 http://127.0.0.1:8080 即可浏览谱面列表 / 详情 / 标签（乱黄、散点等）。
数据来自 sqlite（dance3.sqlite3），爬取过程中可实时刷新查看进度。
"""
import argparse
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import db


class App:
    """内存索引：歌曲列表 + 按 music_id 取完整记录。"""

    def __init__(self, conn):
        self.conn = conn
        self.reload()

    def reload(self):
        """重建内存索引；爬取进行中可定时调用以展示最新进度。"""
        self.songs = []          # 轻量列表（用于表格）
        self.tag_counts = {}
        for row in self.conn.execute(
            "SELECT music_id, data, info_done, beatmaps_done, downloaded FROM songs ORDER BY music_id"
        ):
            rec = json.loads(row["data"])
            info = rec.get("GoodsInfo") or {}
            levels = sorted({
                lv.get("MusicLevel")
                for lv in info.get("LevelList", [])
                if lv.get("MusicLev", -1) >= 0 and lv.get("MusicLevel", -1) > 0
            })
            tags = rec.get("Tags") or rec.get("TagList") or []
            for t in tags:
                self.tag_counts[t] = self.tag_counts.get(t, 0) + 1
            self.songs.append({
                "music_id": row["music_id"],
                "goods_id": rec.get("GoodsID"),
                "name": rec.get("GoodsName", ""),
                "owner": rec.get("OwnerName", ""),
                "tags": tags,
                "levels": levels,
                "n_maps": len(rec.get("BeatMaps") or []),
                "info_done": bool(row["info_done"]),
                "beatmaps_done": bool(row["beatmaps_done"]),
                "downloaded": bool(row["downloaded"]),
            })

    def stats(self):
        self.reload()
        s = self.songs
        return {
            "total": len(s),
            "info_done": sum(1 for x in s if x["info_done"]),
            "beatmaps_done": sum(1 for x in s if x["beatmaps_done"]),
            "downloaded": sum(1 for x in s if x["downloaded"]),
            "n_maps": sum(x["n_maps"] for x in s),
            "tags": sorted(self.tag_counts.items(), key=lambda kv: -kv[1]),
        }

    def search(self, q, tag, status, page, size):
        q = (q or "").strip().lower()
        out = []
        for x in self.songs:
            if q and q not in x["name"].lower() and q not in str(x["music_id"]) and q not in str(x["goods_id"]):
                continue
            if tag and tag not in x["tags"]:
                continue
            if status == "info" and not x["info_done"]:
                continue
            if status == "beatmaps" and not x["beatmaps_done"]:
                continue
            if status == "downloaded" and not x["downloaded"]:
                continue
            out.append(x)
        total = len(out)
        start = (page - 1) * size
        return out[start:start + size], total

    def full(self, music_id):
        rec = db.load(self.conn, music_id)
        if rec is None:
            return None
        info = rec.get("GoodsInfo") or {}
        return {
            "music_id": rec.get("MusicID"),
            "goods_id": rec.get("GoodsID"),
            "name": rec.get("GoodsName", ""),
            "owner": rec.get("OwnerName", ""),
            "tags": rec.get("Tags") or rec.get("TagList") or [],
            "audio_url": rec.get("AudioUrl"),
            "bpm": info.get("BPM"),
            "begin_seconds": info.get("BeginSeconds"),
            "pic": rec.get("PicPath"),
            "intro": rec.get("GoodsIntro"),
            "levels": info.get("LevelList"),
            "beatmaps": rec.get("BeatMaps") or [],
            "info_done": True,
        }


HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>舞立方谱面列表</title>
<style>
body{font-family:"Microsoft YaHei",system-ui,sans-serif;margin:0;background:#f4f6fa;color:#222}
header{background:#1f2937;color:#fff;padding:12px 20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
header h1{font-size:18px;margin:0}
.badge{background:#374151;border-radius:10px;padding:2px 10px;font-size:12px}
#stats{display:flex;gap:10px;flex-wrap:wrap;padding:10px 20px 0}
#stats .card{background:#fff;border-radius:8px;padding:6px 14px;box-shadow:0 1px 2px rgba(0,0,0,.08);font-size:13px}
#stats b{color:#2563eb}
.toolbar{display:flex;gap:8px;padding:12px 20px;flex-wrap:wrap;align-items:center}
input,select,button{padding:7px 10px;border:1px solid #cbd5e1;border-radius:6px;font-size:13px}
input#q{width:260px}
button{cursor:pointer;background:#2563eb;color:#fff;border:none}
table{width:100%;border-collapse:collapse;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.08)}
th,td{padding:8px 10px;border-bottom:1px solid #eef1f5;font-size:13px;text-align:left}
th{background:#f8fafc;position:sticky;top:0}
tr.clickable{cursor:pointer}
tr.clickable:hover{background:#f0f7ff}
.tag{display:inline-block;background:#e0e7ff;color:#3730a3;border-radius:8px;padding:1px 7px;margin:1px 2px;font-size:12px}
.tag.hot{background:#fee2e2;color:#991b1b}
.lvl{color:#0f766e;font-weight:600}
.done{color:#16a34a}.todo{color:#9ca3af}
.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:10}
.modal{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#fff;border-radius:10px;width:min(860px,94vw);max-height:86vh;overflow:auto;padding:20px;z-index:11;box-shadow:0 10px 40px rgba(0,0,0,.3)}
.modal h2{margin:0 0 6px}
.modal .close{float:right;cursor:pointer;border:none;background:#e5e7eb;border-radius:6px;padding:4px 10px}
.meta{color:#6b7280;font-size:13px;margin:4px 0}
.pager{padding:10px 20px;font-size:13px;color:#6b7280}
#pager button{margin-left:6px}
audio{width:100%;margin-top:6px}
</style>
</head>
<body>
<header>
  <h1>舞立方谱面列表</h1>
  <span class="badge" id="dbname"></span>
  <span class="badge" id="realtime"></span>
</header>
<div id="stats"></div>
<div class="toolbar">
  <input id="q" placeholder="搜索名称 / MusicID / GoodsID" oninput="debounced()">
  <select id="tag" onchange="load()"><option value="">全部标签</option></select>
  <select id="status" onchange="load()">
    <option value="">全部状态</option>
    <option value="info">详情已抓</option>
    <option value="beatmaps">谱面已解析</option>
    <option value="downloaded">已下载</option>
  </select>
  <button onclick="load()">刷新</button>
</div>
<table>
  <thead><tr><th>MusicID</th><th>GoodsID</th><th>名称</th><th>作者</th><th>等级</th><th>标签</th><th>谱面数</th><th>状态</th></tr></thead>
  <tbody id="rows"></tbody>
</table>
<div class="pager" id="pager"></div>

<div class="modal-bg" id="mbg" onclick="closeModal()"></div>
<div class="modal" id="modal" style="display:none"></div>

<script>
let PAGE=1, SIZE=50;
const $=id=>document.getElementById(id);
function debounced(){clearTimeout(window._t);window._t=setTimeout(()=>{PAGE=1;load()},300);}
async function jget(u){const r=await fetch(u);return r.json();}
async function load(){
  const q=$('q').value, tag=$('tag').value, st=$('status').value;
  const d=await jget(`/api/songs?q=${encodeURIComponent(q)}&tag=${encodeURIComponent(tag)}&status=${st}&page=${PAGE}&size=${SIZE}`);
  const rows=$('rows'); rows.innerHTML='';
  for(const s of d.items){
    const tr=document.createElement('tr'); tr.className='clickable';
    tr.onclick=()=>openSong(s.music_id);
    const tags=s.tags.map(t=>`<span class="tag">${t}</span>`).join('');
    const stt=`<span class="${s.downloaded?'done':'todo'}">${s.downloaded?'已下载':(s.beatmaps_done?'谱面就绪':(s.info_done?'详情就绪':'待抓'))}</span>`;
    tr.innerHTML=`<td>${s.music_id}</td><td>${s.goods_id}</td><td>${esc(s.name)}</td><td>${esc(s.owner)}</td>`+
      `<td class="lvl">${(s.levels||[]).join('/')}</td><td>${tags||'-'}</td><td>${s.n_maps}</td><td>${stt}</td>`;
    rows.appendChild(tr);
  }
  const pg=$('pager');
  pg.innerHTML=`共 ${d.total} 首，第 ${d.page}/${d.pages} 页`+
    `<button onclick="PAGE=1;load()">首页</button>`+
    `<button onclick="PAGE=Math.max(1,PAGE-1);load()">上一页</button>`+
    `<button onclick="PAGE=Math.min(${d.pages},PAGE+1);load()">下一页</button>`;
}
async function openSong(mid){
  const d=await jget(`/api/song/${mid}`);
  $('modal').style.display='block'; $('mbg').style.display='block';
  const tags=(d.tags||[]).map(t=>`<span class="tag">${t}</span>`).join(' ');
  const maps=(d.beatmaps||[]).map((b,i)=>`<tr><td>${i+1}</td><td class="lvl">${b.Level}</td><td>${esc((b.Url||'').split('/').pop())}</td>`+
    `<td>${(b.Tags||[]).map(t=>`<span class="tag">${t}</span>`).join('')||'-'}</td><td>${b.IsBad?'<span style="color:#b91c1c">坏</span>':'好'}</td></tr>`).join('');
  $('modal').innerHTML=`<button class="close" onclick="closeModal()">关闭</button>
    <h2>${esc(d.name)} <span style="font-size:13px;color:#6b7280">#${d.goods_id}</span></h2>
    <div class="meta">MusicID=${d.music_id} · 作者 ${esc(d.owner)} · BPM ${d.bpm} · 起跳 ${d.begin_seconds}s</div>
    <div class="meta">标签：${tags||'-'}</div>
    <div class="meta">${esc(d.intro||'')}</div>
    <h3 style="margin-bottom:4px">谱面（${(d.beatmaps||[]).length} 张）</h3>
    <table><thead><tr><th>#</th><th>等级</th><th>文件名</th><th>标签</th><th>状态</th></tr></thead><tbody>${maps||'<tr><td colspan=5>-</td></tr>'}</tbody></table>
    <div class="meta" style="margin-top:8px">音频：${esc((d.audio_url||'').split('/').pop()||'-')}</div>
    <audio controls src="${esc(d.audio_url||'')}"></audio>`;
}
function closeModal(){$('modal').style.display='none';$('mbg').style.display='none';}
function esc(s){return (s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
(async function init(){
  function renderStats(st){
    $('stats').innerHTML=`<div class="card">总数 <b>${st.total}</b></div>`+
      `<div class="card">详情已抓 <b>${st.info_done}</b></div>`+
      `<div class="card">谱面已解析 <b>${st.beatmaps_done}</b></div>`+
      `<div class="card">已下载 <b>${st.downloaded}</b>（${st.n_maps} 张谱面）</div>`+
      `<div class="card">热门标签 ${st.tags.slice(0,12).map(([t,c])=>`<span class="tag ${c>100?'hot':''}">${t}×${c}</span>`).join('')||'-'}</div>`;
  }
  $('dbname').textContent='db: '+(await jget('/api/db')).path;
  const st=await jget('/api/stats');
  renderStats(st);
  const sel=$('tag');
  st.tags.forEach(([t])=>{const o=document.createElement('option');o.value=t;o.textContent=t;sel.appendChild(o);});
  load();
  setInterval(async()=>{
    $('realtime').textContent='更新: '+new Date().toLocaleTimeString();
    const s=await jget('/api/stats');
    renderStats(s);
    const rows=$('rows');
    if(rows.children.length===0) load();
  },15000);
})();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    app = None

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path
        qs = parse_qs(u.query)
        if path == "/":
            return self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/api/db":
            return self._send(200, {"path": db.DB_PATH})
        if path == "/api/stats":
            return self._send(200, self.app.stats())
        if path == "/api/songs":
            page = max(1, int(qs.get("page", ["1"])[0]))
            size = min(200, max(10, int(qs.get("size", ["50"])[0])))
            q = qs.get("q", [""])[0]
            tag = qs.get("tag", [""])[0]
            status = qs.get("status", [""])[0]
            items, total = self.app.search(q, tag, status, page, size)
            return self._send(200, {"items": items, "total": total, "page": page, "pages": max(1, -(-total // size))})
        if path.startswith("/api/song/"):
            mid = int(path.rsplit("/", 1)[1])
            d = self.app.full(mid)
            if d is None:
                return self._send(404, {"error": "not found"})
            return self._send(200, d)
        return self._send(404, {"error": "not found"})


def main():
    parser = argparse.ArgumentParser(description="舞立方谱面列表 Web 界面")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--db", default=db.DB_PATH)
    args = parser.parse_args()

    conn = db.get_conn(args.db)
    Handler.app = App(conn)
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"舞立方谱面列表 UI: http://{args.host}:{args.port}  (db={args.db}, songs={len(Handler.app.songs)})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    main()
