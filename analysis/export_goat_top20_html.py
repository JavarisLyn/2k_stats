# -*- coding: utf-8 -*-
"""生成综合 GOAT Top20 精美 HTML 页面。"""
import csv
import html
import json
import os
import urllib.request
from datetime import date

from config import RESULTS

COMBINED_CSV = os.path.join(RESULTS, "goat_scores_combined.csv")
HONORS_CSV = os.path.join(RESULTS, "player_honors_all.csv")
OUT_HTML = os.path.join(RESULTS, "goat_top20.html")
ASSETS_DIR = os.path.join(RESULTS, "assets", "headshots")

# NBA 官方高清头像 1040×760 + 裁剪焦点（object-position）
NBA_PHOTOS = {
    ("Kobe", "Bryant"): (977, "center 8%"),
    ("Michael", "Jordan"): (893, "center 10%"),
    ("Tim", "Duncan"): (1495, "center 12%"),
    ("LeBron", "James"): (2544, "center 10%"),
    ("Kareem", "Abdul-Jabbar"): (76003, "center 12%"),
    ("Wilt", "Chamberlain"): (76375, "center 15%"),
    ("Magic", "Johnson"): (77142, "center 10%"),
    ("Shaquille", "O'Neal"): (406, "center 6%"),
    ("Chris", "Paul"): (101108, "center 10%"),
    ("Larry", "Bird"): (1449, "center 12%"),
    ("Hakeem", "Olajuwon"): (165, "center 10%"),
    ("Carmelo", "Anthony"): (2546, "center 10%"),
    ("Kevin", "Garnett"): (708, "center 10%"),
    ("Dwyane", "Wade"): (2548, "center 10%"),
    ("Oscar", "Robertson"): (78370, "center 18%"),
    ("Kevin", "Durant"): (201142, "center 10%"),
    ("Jerry", "West"): (78497, "center 12%"),
    ("Karl", "Malone"): (252, "center 12%"),
    ("Bob", "Pettit"): (78001, "center 15%"),
    ("Moses", "Malone"): (766, "center 12%"),
    ("Dwight", "Howard"): (2730, "center 8%"),
    ("Bill", "Russell"): (78049, "center 12%"),
    ("James", "Harden"): (201935, "center 10%"),
    ("John", "Stockton"): (304, "center 12%"),
    ("John", "Havlicek"): (76977, "center 15%"),
}

NBA_HEADSHOT_URL = "https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"

# NBA CDN 对极少数传奇球员返回剪影占位图，改用 BBRef 真实照片
FALLBACK_JPG = {
    ("Oscar", "Robertson"): "https://www.basketball-reference.com/req/202106291/images/headshots/roberos01.jpg",
    ("Bob", "Pettit"): "https://www.basketball-reference.com/req/202106291/images/headshots/pettibo01.jpg",
    ("Moses", "Malone"): "https://www.basketball-reference.com/req/202106291/images/headshots/malonmo01.jpg",
    ("Bill", "Russell"): "https://www.basketball-reference.com/req/202106291/images/headshots/russibi01.jpg",
    ("John", "Havlicek"): "https://www.basketball-reference.com/req/202106291/images/headshots/havlijo01.jpg",
}

MIN_PHOTO_BYTES = 20_000

NICKNAME = {
    ("Kobe", "Bryant"): "Black Mamba",
    ("Michael", "Jordan"): "His Airness",
    ("Tim", "Duncan"): "The Big Fundamental",
    ("LeBron", "James"): "King James",
    ("Kareem", "Abdul-Jabbar"): "Captain Skyhook",
    ("Wilt", "Chamberlain"): "Wilt the Stilt",
    ("Magic", "Johnson"): "Magic",
    ("Shaquille", "O'Neal"): "Shaq Diesel",
    ("Chris", "Paul"): "CP3",
    ("Larry", "Bird"): "Larry Legend",
    ("Hakeem", "Olajuwon"): "The Dream",
    ("Carmelo", "Anthony"): "Melo",
    ("Kevin", "Garnett"): "The Big Ticket",
    ("Dwyane", "Wade"): "Flash",
    ("Oscar", "Robertson"): "The Big O",
    ("Kevin", "Durant"): "KD",
    ("Jerry", "West"): "Mr. Clutch",
    ("Karl", "Malone"): "The Mailman",
    ("Bob", "Pettit"): "Bob Pettit",
    ("Moses", "Malone"): "Chairman of the Boards",
    ("Dwight", "Howard"): "Superman",
    ("Bill", "Russell"): "The Chief",
    ("James", "Harden"): "The Beard",
    ("John", "Stockton"): "Stockton to Malone",
    ("John", "Havlicek"): "Hondo",
}

def player_slug(first, last):
    return f"{first}-{last}".lower().replace("'", "").replace(" ", "-")


def nba_cdn_url(player_id):
    return NBA_HEADSHOT_URL.format(player_id=player_id)


def download_headshots(player_keys):
    """下载 Top20 球员高清头像到 results/assets/headshots/。"""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")]
    urllib.request.install_opener(opener)

    paths = {}
    for key in player_keys:
        if key not in NBA_PHOTOS and key not in FALLBACK_JPG:
            continue
        slug = player_slug(key[0], key[1])
        local_png = os.path.join(ASSETS_DIR, f"{slug}.png")
        local_jpg = os.path.join(ASSETS_DIR, f"{slug}.jpg")
        rel_png = f"assets/headshots/{slug}.png"
        rel_jpg = f"assets/headshots/{slug}.jpg"

        if os.path.isfile(local_jpg) and os.path.getsize(local_jpg) >= 5000:
            paths[key] = rel_jpg
            continue
        if os.path.isfile(local_png) and os.path.getsize(local_png) >= MIN_PHOTO_BYTES:
            paths[key] = rel_png
            continue

        saved = False
        meta = NBA_PHOTOS.get(key)
        if meta:
            player_id, _ = meta
            url = nba_cdn_url(player_id)
            try:
                with urllib.request.urlopen(url, timeout=30) as resp:
                    data = resp.read()
                if len(data) >= MIN_PHOTO_BYTES:
                    with open(local_png, "wb") as f:
                        f.write(data)
                    paths[key] = rel_png
                    saved = True
                    print(f"  saved {rel_png} ({len(data) // 1024} KB)")
            except OSError as e:
                print(f"  warn {slug} NBA: {e}")

        if not saved:
            fb = FALLBACK_JPG.get(key)
            if fb:
                try:
                    with urllib.request.urlopen(fb, timeout=30) as resp:
                        data = resp.read()
                    with open(local_jpg, "wb") as f:
                        f.write(data)
                    paths[key] = rel_jpg
                    saved = True
                    print(f"  saved {rel_jpg} fallback ({len(data) // 1024} KB)")
                except OSError as e:
                    print(f"  warn {slug} fallback: {e}")

        if not saved:
            paths[key] = rel_png if os.path.isfile(local_png) else ""

    return paths


def photo_meta(first, last, photo_paths):
    key = (first, last)
    meta = NBA_PHOTOS.get(key)
    pos = meta[1] if meta else "center 15%"
    return photo_paths.get(key, ""), pos


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fmt_num(val, digits=1):
    if val is None or str(val).strip() == "":
        return "—"
    return f"{float(val):.{digits}f}"


def score_bar_values(p):
    return f"{p['honor_norm']:.0f}", f"{p['stats_norm']:.0f}"


def render_bars(p, compact=False):
    honor_txt, stats_txt = score_bar_values(p)
    cls = "bars compact with-values" if compact else "bars"
    return f"""
        <div class="{cls}">
          <div class="bar-row">
            <span>荣誉</span>
            <div class="bar"><i style="width:{p['honor_norm']:.1f}%"></i></div>
            <em>{honor_txt}</em>
          </div>
          <div class="bar-row">
            <span>数据</span>
            <div class="bar bar-stats"><i style="width:{p['stats_norm']:.1f}%"></i></div>
            <em>{stats_txt}</em>
          </div>
        </div>"""


def honor_badges(h):
    badges = []
    mapping = [
        ("MVP", "MVP", "mvp"),
        ("FMVP", "FMVP", "fmvp"),
        ("总冠军", "RING", "ring"),
        ("得分王", "SCORING", "scoring"),
        ("篮板王", "REB", "reb"),
        ("助攻王", "AST", "ast"),
        ("抢断王", "STL", "stl"),
        ("盖帽王", "BLK", "blk"),
        ("最佳一阵", "1ST TEAM", "team"),
        ("防一阵", "DEF 1ST", "def1"),
        ("最佳防守球员", "DPOY", "dpoy"),
    ]
    for col, label, cls in mapping:
        n = int(h.get(col, 0) or 0)
        if n:
            badges.append({"label": label, "count": n, "cls": cls})
    return badges


def build_players(photo_paths):
    combined = load_csv(COMBINED_CSV)[:20]
    honors = {(r["名字"], r["姓氏"]): r for r in load_csv(HONORS_CSV)}

    players = []
    for i, row in enumerate(combined, 1):
        first, last = row["名字"], row["姓氏"]
        key = (first, last)
        h = honors.get(key, {})
        photo, photo_pos = photo_meta(first, last, photo_paths)
        players.append({
            "rank": i,
            "first": first,
            "last": last,
            "name": f"{first} {last}",
            "nickname": NICKNAME.get(key, ""),
            "photo": photo,
            "photo_pos": photo_pos,
            "combined": float(row["goat_score_combined"]),
            "honor_score": float(row["荣誉分"]),
            "honor_norm": float(row["荣誉归一化"]),
            "stats_score_val": float(row["数据分"]) if str(row.get("数据分", "")).strip() else None,
            "stats_score": fmt_num(row.get("数据分"), 2),
            "stats_norm": float(row["数据归一化"]) if row.get("数据归一化") != "" else 0,
            "ppg": fmt_num(h.get("场均得分")),
            "rpg": fmt_num(h.get("场均篮板")),
            "apg": fmt_num(h.get("场均助攻")),
            "games": h.get("出场总数") or "—",
            "badges": honor_badges(h),
        })
        if not photo:
            print(f"  warn: 无头像 #{i} {first} {last}")
    return players


def render_podium_card(p, tier):
    badges_html = "".join(
        f'<span class="badge badge-{b["cls"]}">{b["label"]} {b["count"]}</span>'
        for b in p["badges"]
    )
    return f"""
    <article class="podium-card tier-{tier}" data-rank="{p['rank']}">
      <div class="rank-medal">#{p['rank']}</div>
      <div class="photo-wrap" style="--photo-pos: {html.escape(p['photo_pos'])}">
        <img class="player-photo" src="{html.escape(p['photo'])}" alt="{html.escape(p['name'])}" loading="eager" decoding="async">
        <div class="photo-glow"></div>
      </div>
      <div class="podium-body">
        <h2>{html.escape(p['name'])}</h2>
        <p class="nickname">{html.escape(p['nickname'])}</p>
        <div class="score-main">{p['combined']:.1f}</div>
        <p class="score-label">综合 GOAT 分</p>
        {render_bars(p)}
        <div class="stat-line">
          <span>{p['ppg']} PTS</span>
          <span>{p['rpg']} REB</span>
          <span>{p['apg']} AST</span>
          <span>{p['games']} GP</span>
        </div>
        <div class="badges">{badges_html}</div>
      </div>
    </article>"""


def render_champion_card(p):
    badges_html = "".join(
        f'<span class="badge badge-{b["cls"]}">{b["label"]} {b["count"]}</span>'
        for b in p["badges"]
    )
    return f"""
    <article class="champion-card" data-rank="1">
      <div class="champion-crown">#1 · GOAT</div>
      <div class="champion-inner">
        <div class="champion-photo" style="--photo-pos: {html.escape(p['photo_pos'])}">
          <img class="player-photo" src="{html.escape(p['photo'])}" alt="{html.escape(p['name'])}" loading="eager" decoding="async">
          <div class="photo-glow"></div>
        </div>
        <div class="champion-body">
          <h2>{html.escape(p['name'])}</h2>
          <p class="nickname">{html.escape(p['nickname'])}</p>
          <div class="score-main champion-score">{p['combined']:.1f}</div>
          <p class="score-label">综合 GOAT 分</p>
          <div class="bars">
            <div class="bar-row">
              <span>荣誉</span>
              <div class="bar"><i style="width:{p['honor_norm']:.1f}%"></i></div>
              <em>{p['honor_norm']:.0f}</em>
            </div>
            <div class="bar-row">
              <span>数据</span>
              <div class="bar bar-stats"><i style="width:{p['stats_norm']:.1f}%"></i></div>
              <em>{p['stats_norm']:.0f}</em>
            </div>
          </div>
          <div class="stat-line">
            <span>{p['ppg']} PTS</span>
            <span>{p['rpg']} REB</span>
            <span>{p['apg']} AST</span>
            <span>{p['games']} GP</span>
          </div>
          <div class="badges">{badges_html}</div>
        </div>
      </div>
    </article>"""


def render_grid_card(p):
    badges_html = "".join(
        f'<span class="badge badge-{b["cls"]}">{b["label"]} {b["count"]}</span>'
        for b in p["badges"]
    )
    return f"""
    <article class="grid-card" data-rank="{p['rank']}">
      <div class="grid-rank">#{p['rank']:02d}</div>
      <div class="grid-photo" style="--photo-pos: {html.escape(p['photo_pos'])}">
        <img class="player-photo" src="{html.escape(p['photo'])}" alt="{html.escape(p['name'])}" loading="lazy" decoding="async">
      </div>
      <div class="grid-info">
        <div class="grid-head">
          <div>
            <h3>{html.escape(p['name'])}</h3>
            <p class="nickname-sm">{html.escape(p['nickname'])}</p>
          </div>
          <div class="grid-score">{p['combined']:.1f}</div>
        </div>
        {render_bars(p, compact=True)}
        <div class="stat-line sm">
          <span>{p['ppg']}/{p['rpg']}/{p['apg']}</span>
          <span>{p['games']} GP</span>
        </div>
        <div class="badges">{badges_html}</div>
      </div>
    </article>"""


def render_html(players):
    champion_html = render_champion_card(players[0]) if players else ""
    elite_html = "".join(
        render_podium_card(p, 2 if p["rank"] == 2 else 3 if p["rank"] == 3 else 4)
        for p in players[1:5]
    )
    grid_html = "".join(render_grid_card(p) for p in players[5:])

    data_json = json.dumps(players, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GOAT Score · 综合 Top 20</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+SC:wght@400;500;700&family=Oswald:wght@500;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #070b14;
      --surface: #0f1628;
      --surface2: #151f36;
      --gold: #d4af37;
      --gold-light: #f0d875;
      --silver: #c0c8d8;
      --bronze: #cd7f32;
      --accent: #3d8bfd;
      --text: #eef2ff;
      --muted: #8b9bb4;
      --border: rgba(255,255,255,.08);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Noto Sans SC", system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      overflow-x: hidden;
    }}
    .bg {{
      position: fixed; inset: 0; z-index: 0; pointer-events: none;
      background:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(212,175,55,.18), transparent),
        radial-gradient(ellipse 60% 40% at 100% 50%, rgba(61,139,253,.08), transparent),
        radial-gradient(ellipse 50% 30% at 0% 80%, rgba(212,175,55,.06), transparent),
        var(--bg);
    }}
    .court-lines {{
      position: fixed; inset: 0; z-index: 0; opacity: .04; pointer-events: none;
      background-image:
        linear-gradient(90deg, #fff 1px, transparent 1px),
        linear-gradient(#fff 1px, transparent 1px);
      background-size: 80px 80px;
    }}
    .wrap {{ position: relative; z-index: 1; max-width: 1280px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }}

    header {{
      text-align: center; padding: 2.5rem 1rem 3rem;
    }}
    .eyebrow {{
      font-family: Oswald, sans-serif; letter-spacing: .35em; font-size: .75rem;
      color: var(--gold); text-transform: uppercase; margin-bottom: .75rem;
    }}
    h1 {{
      font-family: "Bebas Neue", sans-serif;
      font-size: clamp(3rem, 10vw, 5.5rem);
      line-height: .95;
      background: linear-gradient(180deg, #fff 30%, var(--gold-light) 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    .subtitle {{
      margin-top: 1rem; color: var(--muted); font-size: .95rem; max-width: 36rem; margin-inline: auto; line-height: 1.6;
    }}
    .formula {{
      display: inline-flex; gap: .5rem; flex-wrap: wrap; justify-content: center;
      margin-top: 1.25rem; padding: .5rem 1rem;
      background: rgba(255,255,255,.04); border: 1px solid var(--border); border-radius: 999px;
      font-size: .8rem; color: var(--muted);
    }}
    .formula strong {{ color: var(--gold-light); }}

    .champion-row {{
      display: flex; justify-content: center;
      margin-bottom: 2.5rem;
    }}
    .champion-card {{
      width: 100%; max-width: 760px;
      background: linear-gradient(165deg, #1a2238, var(--surface));
      border: 1px solid rgba(212,175,55,.4);
      border-radius: 1.5rem;
      overflow: hidden;
      position: relative;
      box-shadow: 0 28px 70px rgba(212,175,55,.22), 0 0 0 1px rgba(212,175,55,.08) inset;
    }}
    .champion-crown {{
      text-align: center;
      font-family: Oswald, sans-serif;
      font-size: .8rem;
      letter-spacing: .28em;
      color: #1a1200;
      background: linear-gradient(90deg, #a8841a, var(--gold-light), #a8841a);
      padding: .55rem 1rem;
      font-weight: 700;
    }}
    .champion-inner {{
      display: grid;
      grid-template-columns: minmax(220px, 42%) 1fr;
      align-items: stretch;
    }}
    @media (max-width: 680px) {{
      .champion-inner {{ grid-template-columns: 1fr; }}
    }}
    .champion-photo {{
      position: relative;
      aspect-ratio: 3/4;
      background: linear-gradient(180deg, #1a2744, #0a0f1a);
      overflow: hidden;
    }}
    .champion-photo .player-photo {{
      transform: scale(1.04);
    }}
    .champion-body {{
      padding: 1.5rem 1.75rem 1.75rem;
      display: flex; flex-direction: column; justify-content: center;
    }}
    .champion-body h2 {{
      font-family: Oswald, sans-serif;
      font-size: clamp(1.6rem, 4vw, 2rem);
      font-weight: 700;
    }}
    .champion-score {{
      font-size: clamp(3.2rem, 8vw, 4rem) !important;
    }}

    .podium {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
      align-items: stretch;
      margin-bottom: 3rem;
    }}
    @media (max-width: 1024px) {{
      .podium {{ grid-template-columns: repeat(2, 1fr); }}
    }}
    @media (max-width: 540px) {{
      .podium {{ grid-template-columns: 1fr; max-width: 420px; margin-inline: auto; }}
    }}

    .podium-card {{
      background: linear-gradient(165deg, var(--surface2), var(--surface));
      border: 1px solid var(--border);
      border-radius: 1.25rem;
      overflow: hidden;
      position: relative;
      transition: transform .35s ease, box-shadow .35s ease;
    }}
    .podium-card:hover {{ transform: translateY(-6px); }}
    .tier-2 {{ border-color: rgba(192,200,216,.25); }}
    .tier-3 {{ border-color: rgba(205,127,50,.25); }}
    .tier-4 {{ border-color: rgba(255,255,255,.1); }}

    .rank-medal {{
      position: absolute; top: 1rem; left: 1rem; z-index: 2;
      font-family: "Bebas Neue", sans-serif; font-size: 1.5rem;
      width: 2.5rem; height: 2.5rem; display: grid; place-items: center;
      border-radius: 50%; background: rgba(0,0,0,.5); backdrop-filter: blur(8px);
    }}
    .tier-1 .rank-medal {{ background: linear-gradient(135deg, var(--gold), #a8841a); color: #1a1200; }}
    .tier-2 .rank-medal {{ background: linear-gradient(135deg, var(--silver), #8a95a8); color: #111; }}
    .tier-3 .rank-medal {{ background: linear-gradient(135deg, var(--bronze), #8b5a2b); color: #111; }}
    .tier-4 .rank-medal {{ background: rgba(255,255,255,.12); color: var(--text); }}

    .podium-section-title {{
      font-family: Oswald, sans-serif;
      font-size: .85rem;
      letter-spacing: .2em;
      color: var(--muted);
      text-align: center;
      margin-bottom: 1rem;
    }}

    .photo-wrap {{
      position: relative; aspect-ratio: 3/4; overflow: hidden;
      background: linear-gradient(180deg, #1a2744, #0a0f1a);
    }}
    .player-photo {{
      width: 100%; height: 100%;
      object-fit: cover;
      object-position: var(--photo-pos, center 12%);
      filter: saturate(1.08) contrast(1.04);
    }}
    .podium-card .player-photo {{
      transform: scale(1.02);
    }}
    .photo-glow {{
      position: absolute; inset: 0;
      background: linear-gradient(to top, var(--surface) 0%, transparent 45%);
    }}

    .podium-body {{ padding: 1.25rem 1.35rem 1.5rem; }}
    .podium-body h2 {{
      font-family: Oswald, sans-serif; font-size: 1.2rem; font-weight: 700; letter-spacing: .02em;
    }}
    .podium .score-main {{ font-size: 2.4rem; }}
    .podium .badges {{ display: none; }}
    @media (min-width: 1025px) {{
      .podium .badges {{ display: flex; }}
    }}
    .nickname {{ color: var(--muted); font-size: .85rem; margin: .15rem 0 .75rem; font-style: italic; }}
    .score-main {{
      font-family: "Bebas Neue", sans-serif; font-size: 3rem; line-height: 1;
      color: var(--gold-light);
    }}
    .score-label {{ font-size: .75rem; color: var(--muted); letter-spacing: .12em; text-transform: uppercase; margin-bottom: 1rem; }}

    .bars {{ display: flex; flex-direction: column; gap: .45rem; margin-bottom: .85rem; }}
    .bars.compact {{ margin-bottom: .5rem; }}
    .bar-row {{
      display: grid; grid-template-columns: 3.2rem 1fr 2rem; gap: .5rem; align-items: center;
      font-size: .72rem; color: var(--muted);
    }}
    .bars.compact .bar-row {{ grid-template-columns: 2rem 1fr; }}
    .bars.compact.with-values .bar-row {{ grid-template-columns: 2rem 1fr 2.4rem; }}
    .bar {{
      height: 6px; background: rgba(255,255,255,.08); border-radius: 999px; overflow: hidden;
    }}
    .bar i {{
      display: block; height: 100%; border-radius: 999px;
      background: linear-gradient(90deg, var(--gold), var(--gold-light));
    }}
    .bar-stats i {{ background: linear-gradient(90deg, #2563eb, var(--accent)); }}
    .bar-row em {{ text-align: right; color: var(--text); font-style: normal; font-weight: 600; }}

    .stat-line {{
      display: flex; flex-wrap: wrap; gap: .65rem; font-size: .78rem; color: var(--muted);
      font-family: Oswald, sans-serif; letter-spacing: .04em; margin-bottom: .75rem;
    }}
    .stat-line span {{ padding: .2rem .5rem; background: rgba(255,255,255,.05); border-radius: .35rem; }}
    .stat-line.sm {{ justify-content: space-between; margin-bottom: .5rem; }}

    .badges {{ display: flex; flex-wrap: wrap; gap: .35rem; }}
    .badge {{
      font-size: .65rem; font-weight: 700; letter-spacing: .06em;
      padding: .25rem .45rem; border-radius: .3rem; text-transform: uppercase;
    }}
    .badge-mvp {{ background: rgba(212,175,55,.2); color: var(--gold-light); }}
    .badge-fmvp {{ background: rgba(255,215,0,.15); color: #ffe566; }}
    .badge-ring {{ background: rgba(255,255,255,.1); color: #fff; }}
    .badge-scoring {{ background: rgba(239,68,68,.15); color: #fca5a5; }}
    .badge-reb {{ background: rgba(249,115,22,.15); color: #fdba74; }}
    .badge-ast {{ background: rgba(168,85,247,.15); color: #d8b4fe; }}
    .badge-stl {{ background: rgba(14,165,233,.15); color: #7dd3fc; }}
    .badge-blk {{ background: rgba(99,102,241,.15); color: #a5b4fc; }}
    .badge-team {{ background: rgba(59,130,246,.15); color: #93c5fd; }}
    .badge-dpoy {{ background: rgba(34,197,94,.15); color: #86efac; }}
    .badge-def1 {{ background: rgba(16,185,129,.12); color: #6ee7b7; }}

    .section-title {{
      font-family: Oswald, sans-serif; font-size: 1.25rem; letter-spacing: .15em;
      color: var(--muted); margin-bottom: 1.25rem; padding-left: .25rem;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 1rem;
    }}

    .grid-card {{
      display: grid; grid-template-columns: 7rem 1fr;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 1rem;
      overflow: hidden;
      transition: border-color .3s, transform .3s;
    }}
    .grid-card:hover {{
      border-color: rgba(212,175,55,.25);
      transform: translateY(-3px);
    }}
    .grid-rank {{
      position: absolute; margin: .65rem; z-index: 1;
      font-family: "Bebas Neue", sans-serif; font-size: 1.1rem;
      color: var(--muted);
    }}
    .grid-card {{ position: relative; }}
    .grid-photo {{
      background: #1a2744;
      overflow: hidden;
      min-height: 7.5rem;
      align-self: stretch;
    }}
    .grid-photo .player-photo {{
      transform: scale(1.08);
    }}
    .grid-info {{ padding: .85rem .9rem .9rem 0; min-width: 0; }}
    .grid-head {{ display: flex; justify-content: space-between; align-items: flex-start; gap: .5rem; margin-bottom: .45rem; }}
    .grid-head h3 {{ font-family: Oswald, sans-serif; font-size: 1rem; line-height: 1.2; }}
    .nickname-sm {{ font-size: .72rem; color: var(--muted); font-style: italic; }}
    .grid-score {{
      font-family: "Bebas Neue", sans-serif; font-size: 1.75rem; color: var(--gold-light); line-height: 1;
    }}

    footer {{
      margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--border);
      text-align: center; color: var(--muted); font-size: .8rem; line-height: 1.8;
    }}
    footer a {{ color: var(--gold); text-decoration: none; }}
  </style>
</head>
<body>
  <div class="bg"></div>
  <div class="court-lines"></div>
  <div class="wrap">
    <header>
      <p class="eyebrow">NBA 2K26 · Stats Project</p>
      <h1>GOAT SCORE<br>TOP 20</h1>
      <p class="subtitle">
        综合版排名：荣誉与生涯数据经 Min-Max 归一化后，按 <strong>6.5 : 3.5</strong> 加权合并。
        荣誉数据来自 2K 模拟；1976 及以前赛季荣誉 ×0.7。
      </p>
      <div class="formula">
        <span>综合分 =</span>
        <strong>0.65 × 荣誉归一化</strong>
        <span>+</span>
        <strong>0.35 × 数据归一化</strong>
      </div>
    </header>

    <section class="champion-row" aria-label="#1 GOAT">
      {champion_html}
    </section>

    <p class="podium-section-title">#2 — #5</p>
    <section class="podium" aria-label="Top 2 to 5">
      {elite_html}
    </section>

    <h2 class="section-title">#6 — #20</h2>
    <section class="grid" aria-label="Rank 6 to 20">
      {grid_html}
    </section>

    <footer>
      <p>生成日期 {date.today().isoformat()} · 数据源 2K Roster Editor Extract</p>
      <p>球员照片：NBA 官方 headshot（1040×760）· 算法详见 algo.md</p>
    </footer>
  </div>
  <script type="application/json" id="goat-data">{data_json}</script>
</body>
</html>"""


def main():
    combined = load_csv(COMBINED_CSV)[:20]
    keys = [(r["名字"], r["姓氏"]) for r in combined]
    print("Downloading headshots…")
    photo_paths = download_headshots(keys)
    players = build_players(photo_paths)
    content = render_html(players)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {OUT_HTML} ({len(players)} players)")


if __name__ == "__main__":
    main()
