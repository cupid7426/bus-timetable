"""国際興業バスの時刻表(NAVITIME)を取得し docs/data.json を生成する。"""
import json, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://transfer-cloud.navitime.biz/5931bus/courses/timetables?busstop={busstop}&course-sequence={course}"
HOLIDAYS = "https://holidays-jp.github.io/api/v1/date.json"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (bus-timetable personal use)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def resolve(arr, i):
    v = arr[i]
    if isinstance(v, list):
        if v and v[0] in ("ShallowReactive", "Reactive", "Ref", "ShallowRef"):
            return resolve(arr, v[1])
        return [resolve(arr, x) for x in v]
    if isinstance(v, dict):
        return {k: resolve(arr, x) for k, x in v.items()}
    return v


def parse(html):
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    arr = json.loads(m.group(1))
    # 時刻表データは bff:...busstops/timetables のエントリ
    root = resolve(arr, 2)
    key = next(k for k in root if "busstops" in k and "timetables" in k)
    return root[key]


def main():
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    out = {"weekday": [], "saturday": [], "holiday": []}
    info = {}
    for s in cfg["stops"]:
        data = parse(get(URL.format(**s)))
        for reg in data["regular"]:
            if s["no"] not in info:
                text = reg["courseGroupDestination"] + " ".join(n for sc in reg["schedules"] for n in sc["notes"])
                m = re.search(r"（(.+?のりば)発）", reg["courseGroupDestination"]) or re.search(r"(体育館通りのりば|[^、※＼\s]+のりば)の時刻表", text)
                m2 = re.search(r"上記便は(.+?)よりまいります", text)
                info[s["no"]] = {"name": s["name"], "landmark": m.group(1) if m else "",
                                 "from": m2.group(1) if m2 else "", "lat": data["latitude"], "lon": data["longitude"]}
            for sch in reg["schedules"]:
                t = sch["scheduleType"]
                if t not in out:
                    continue
                for trip in sch["trips"]:
                    if "赤羽駅" not in trip["destination"]:
                        continue  # 赤羽車庫行きなど駅に行かない便は除外
                    dep = trip["departureTime"]  # 2026-10-05T17:11:00+09:00
                    out[t].append({
                        "stop": s["no"],
                        "time": dep[11:16],
                        "line": trip["courseName"],
                        "dest": trip["destination"],
                    })
    for t in out:
        out[t].sort(key=lambda x: (x["time"], x["stop"]))
        if not out[t]:
            sys.exit(f"{t}: データが0件です。ページ構造が変わった可能性があります")
    try:
        hol = sorted(json.loads(get(HOLIDAYS)).keys())
    except Exception as e:
        print("祝日取得失敗(前回値を維持):", e)
        old = ROOT / "docs" / "data.json"
        hol = json.loads(old.read_text(encoding="utf-8")).get("holidays", []) if old.exists() else []
    from datetime import datetime, timezone, timedelta
    jst = timezone(timedelta(hours=9))
    result = {"updated": datetime.now(jst).strftime("%Y-%m-%d %H:%M"),
              "stops": {str(s["no"]): s["name"] for s in cfg["stops"]},
              "stop_info": {str(k): v for k, v in sorted(info.items())},
              "holidays": hol, "timetable": out}
    (ROOT / "docs" / "data.json").write_text(json.dumps(result, ensure_ascii=False, indent=0), encoding="utf-8")
    print({k: len(v) for k, v in out.items()})


if __name__ == "__main__":
    main()
