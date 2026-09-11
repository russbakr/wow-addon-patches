#!/usr/bin/env python3
"""Vitalog morning sync: pull Oura and parse Apple Health e-mails into daily metrics.

Usage:
  python3 sync.py --oura-token TOKEN [--days 14] [--health-mail FILE ...]

Prints JSON: {"daily": {"YYYY-MM-DD": {"metric": value, "_s": {"metric": "oura"|"apple"|"hume"|"mfp"}}}, "log": [...]}
Metric names match the Vitalog app (METRICS in index.html). No third-party packages needed.
"""
import argparse, datetime as dt, json, re, sys, urllib.parse, urllib.request

OURA = "https://api.ouraring.com/v2/usercollection/"
KG_LB = 2.2046226218

def oura_get(token, path, start, end):
    url = OURA + path + "?" + urllib.parse.urlencode({"start_date": start, "end_date": end})
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r).get("data", [])

def put(daily, day, field, value, src):
    if value is None:
        return
    try:
        value = float(value)
    except (TypeError, ValueError):
        return
    d = daily.setdefault(day, {"_s": {}})
    d[field] = round(value, 3)
    d["_s"][field] = src

def pull_oura(token, days, daily, log):
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    s, e = start.isoformat(), (end + dt.timedelta(days=1)).isoformat()
    n = 0
    try:
        for row in oura_get(token, "daily_sleep", s, e):
            put(daily, row["day"], "sleepScore", row.get("score"), "oura"); n += 1
        for row in oura_get(token, "daily_readiness", s, e):
            put(daily, row["day"], "readiness", row.get("score"), "oura")
            put(daily, row["day"], "tempDev", row.get("temperature_deviation"), "oura"); n += 1
        for row in oura_get(token, "daily_activity", s, e):
            put(daily, row["day"], "activityScore", row.get("score"), "oura")
            put(daily, row["day"], "steps", row.get("steps"), "oura")
            put(daily, row["day"], "activeCal", row.get("active_calories"), "oura"); n += 1
        for row in oura_get(token, "sleep", s, e):
            if row.get("type") not in (None, "long_sleep"):
                continue
            day = row["day"]
            if row.get("total_sleep_duration"):
                put(daily, day, "sleepHours", row["total_sleep_duration"] / 3600.0, "oura")
            put(daily, day, "hrv", row.get("average_hrv"), "oura")
            put(daily, day, "rhr", row.get("lowest_heart_rate"), "oura")
            put(daily, day, "respRate", row.get("average_breath"), "oura"); n += 1
        try:
            for row in oura_get(token, "daily_spo2", s, e):
                sp = row.get("spo2_percentage") or {}
                put(daily, row["day"], "spo2", sp.get("average"), "oura")
        except Exception as ex:  # spo2 needs its own scope; not fatal
            log.append("Oura SpO2 skipped: %s" % ex)
        log.append("Oura: %d records over %d days" % (n, days))
    except urllib.error.HTTPError as ex:
        body = ex.read().decode("utf-8", "ignore")[:200]
        if ex.code == 401:
            log.append("Oura token rejected (expired or revoked). Reconnect Oura from Vitalog's Sources tab.")
        else:
            log.append("Oura error %s: %s" % (ex.code, body))
    except Exception as ex:
        log.append("Oura failed: %s" % ex)

# ---- Apple Health e-mail (sent by the iPhone Shortcut) ----
ALIASES = [
    (r"^(weight|body mass)$", "weightKg", "weight"),
    (r"^(body fat|body fat percentage)$", "bodyFat", "pct"),
    (r"^(lean body mass|muscle mass)$", "muscleKg", "weight"),
    (r"^(steps|step count)$", "steps", None),
    (r"^(sleep|time asleep|sleep analysis|asleep)$", "sleepHours", "duration"),
    (r"^(hrv|heart rate variability)$", "hrv", None),
    (r"^(resting heart rate|rhr)$", "rhr", None),
    (r"^(respiratory rate|breathing rate)$", "respRate", None),
    (r"^(blood oxygen|oxygen saturation|spo2)$", "spo2", "pct"),
    (r"^(active energy|active calories)$", "activeCal", "energy"),
    (r"^(dietary energy|calories|energy consumed|calories eaten)$", "calories", "energy"),
    (r"^(protein)$", "protein", None),
    (r"^(carbohydrates|carbs)$", "carbs", None),
    (r"^(total fat|fat)$", "fat", None),
    (r"^(fiber|fibre)$", "fiber", None),
    (r"^(sodium)$", "sodium", "sodium"),
    (r"^(water|dietary water)$", "water", "water"),
]

def conv(kind, v, unit):
    u = (unit or "").lower()
    if kind == "weight" and (u.startswith("lb") or (not u and v > 130)):
        return v / KG_LB
    if kind == "pct" and v <= 1:
        return v * 100
    if kind == "duration":
        if "sec" in u or v > 1500: return v / 3600.0
        if "min" in u or v > 30: return v / 60.0
        return v
    if kind == "energy" and u == "kj":
        return v / 4.184
    if kind == "sodium" and u == "g":
        return v * 1000
    if kind == "water":
        if u == "l": return v * 1000
        if u.startswith("fl"): return v * 29.57
        if u in ("cup", "cups"): return v * 240
    return v

def parse_health_mail(text, daily, log, src_default="apple"):
    """Lines like 'Weight: 82.1 kg' or 'Steps: 8,412'. Optional 'Date: 2026-09-10' and 'Source: Hume' lines."""
    day = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    src = src_default
    n = 0
    for line in text.splitlines():
        m = re.match(r"^\s*([A-Za-z][A-Za-z /]+?)\s*[:=]\s*([-\d.,]+)\s*([A-Za-z%/]*)", line)
        if not m:
            continue
        key, val, unit = m.group(1).strip().lower(), m.group(2).replace(",", ""), m.group(3)
        if key == "date":
            continue
        try:
            v = float(val)
        except ValueError:
            continue
        for pat, field, kind in ALIASES:
            if re.match(pat, key):
                put(daily, day, field, conv(kind, v, unit), src); n += 1
                break
    for line in text.splitlines():
        m = re.match(r"^\s*date\s*[:=]\s*(\d{4}-\d{2}-\d{2})", line, re.I)
        if m:
            day = m.group(1)
        m = re.match(r"^\s*source\s*[:=]\s*(\w+)", line, re.I)
        if m:
            s = m.group(1).lower()
            src = "hume" if "hume" in s else "oura" if "oura" in s else "mfp" if "fitness" in s else "apple"
    log.append("Health mail: %d values for %s" % (n, day))
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oura-token", default="")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--health-mail", nargs="*", default=[])
    a = ap.parse_args()
    daily, log = {}, []
    if a.oura_token:
        pull_oura(a.oura_token.split("|")[0], a.days, daily, log)
    for path in a.health_mail:
        with open(path, encoding="utf-8", errors="ignore") as f:
            txt = f.read()
        # honour Date:/Source: lines first
        mday = re.search(r"^\s*date\s*[:=]\s*(\d{4}-\d{2}-\d{2})", txt, re.I | re.M)
        msrc = re.search(r"^\s*source\s*[:=]\s*(\w+)", txt, re.I | re.M)
        tmp = {}
        parse_health_mail(txt, tmp, log)
        day = mday.group(1) if mday else (dt.date.today() - dt.timedelta(days=1)).isoformat()
        s = (msrc.group(1).lower() if msrc else "")
        src = "hume" if "hume" in s else "oura" if "oura" in s else "mfp" if "fitness" in s else "apple"
        for _, vals in tmp.items():
            for f, v in vals.items():
                if f != "_s":
                    put(daily, day, f, v, src)
    json.dump({"daily": daily, "log": log}, sys.stdout, indent=1)

if __name__ == "__main__":
    main()
