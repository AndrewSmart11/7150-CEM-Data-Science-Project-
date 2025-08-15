#!/usr/bin/env python3
"""
Extract two specific T20I matches (IND–PAK 2022 T20WC and ENG–WI 2016 WT20 Final)
from a Cricsheet T20I JSON dump into ball-by-ball CSVs.
Usage:
  python 01_extract_matches.py --zip t20s_json.zip --outdir outputs/
If you've already extracted the zip, pass --jsondir <folder> instead of --zip.
"""
import os, json, csv, zipfile, argparse
from pathlib import Path

TEAM_SYNONYMS = {
    "west indies men": "west indies",
    "windies": "west indies",
    "england men": "england",
    "india men": "india",
    "pakistan men": "pakistan",
}

TARGETS = [
    {
        "label": "IND-PAK 2022 T20WC",
        "outfile": "IND_PAK_2022_T20WC_ball_by_ball.csv",
        "date": "2022-10-23",
        "teams": {"india", "pakistan"},
        "event_contains_any": ["world cup", "t20 world cup", "icc men's t20 world cup"],
    },
    {
        "label": "ENG-WI 2016 WT20 Final",
        "outfile": "ENG_WI_2016_WT20_Final_ball_by_ball.csv",
        "date": "2016-04-03",
        "teams": {"england", "west indies"},
        "event_contains_any": ["world twenty20", "icc world twenty20", "wt20", "world t20"],
    },
]

def norm_team_name(t):
    t = (t or "").strip().lower()
    return TEAM_SYNONYMS.get(t, t)

def norm_event_name(ev):
    if isinstance(ev, dict):
        return str(ev.get("name") or ev.get("match_number") or "").strip().lower()
    return str(ev or "").strip().lower()

def dates_as_str_list(info):
    return [str(d) for d in info.get("dates", [])]

def get_info_teams(info):
    return {norm_team_name(x) for x in info.get("teams", [])}

def match_strength(info, T):
    ds = dates_as_str_list(info)
    ev = norm_event_name(info.get("event"))
    teams = get_info_teams(info)
    score = 0
    if T["date"] in ds:
        score = max(score, 1)
        if teams == T["teams"]:
            score = max(score, 2)
            if any(s in ev for s in T["event_contains_any"]):
                score = max(score, 3)
    return score

def rows_from_legacy_innings(innings_block, info):
    rows = []
    innings_name = list(innings_block.keys())[0]
    innings = innings_block[innings_name]
    batting_team = innings.get("team")

    for d in innings.get("deliveries", []):
        (ball_label, ball) = next(iter(d.items()))
        over_str, ball_str = ball_label.split(".")
        over = int(over_str); ball_in_over = int(ball_str)

        runs = ball.get("runs", {}) or {}
        wicket = ball.get("wicket")
        wickets_list = ball.get("wickets", [])
        wicket_event = bool(wicket or wickets_list)
        dismissal_kind = player_out = None
        if wicket:
            dismissal_kind = wicket.get("kind"); player_out = wicket.get("player_out")
        elif wickets_list:
            wk = wickets_list[0]; dismissal_kind = wk.get("kind"); player_out = wk.get("player_out")

        extras = ball.get("extras", {}) or {}
        extras_type = next(iter(extras.keys())) if extras else None

        rows.append({
            "match_date": (dates_as_str_list(info) or [None])[0],
            "venue": info.get("venue"),
            "city": info.get("city"),
            "event": (info.get("event") or {}).get("name") if isinstance(info.get("event"), dict) else info.get("event"),
            "toss_winner": (info.get("toss") or {}).get("winner"),
            "toss_decision": (info.get("toss") or {}).get("decision"),
            "innings": 1 if "1st" in innings_name else 2,
            "batting_team": batting_team,
            "over": over,
            "ball_in_over": ball_in_over,
            "striker": ball.get("batter") or ball.get("batsman"),
            "non_striker": ball.get("non_striker"),
            "bowler": ball.get("bowler"),
            "runs_batter": runs.get("batter", 0),
            "runs_extras": runs.get("extras", 0),
            "runs_total": runs.get("total", 0),
            "extras_type": extras_type,
            "wicket_event": wicket_event,
            "dismissal_kind": dismissal_kind,
            "player_out": player_out
        })
    return rows

def rows_from_v2_innings(innings_block, info, innings_idx):
    rows = []
    batting_team = innings_block.get("team")
    for over_obj in innings_block.get("overs", []):
        over = int(over_obj.get("over", 0))
        for i, ball in enumerate(over_obj.get("deliveries", []), start=1):
            ball_in_over = int(ball.get("ball", i))
            runs = ball.get("runs", {}) or {}
            wicket = ball.get("wicket")
            wickets_list = ball.get("wickets", [])
            wicket_event = bool(wicket or wickets_list)
            dismissal_kind = player_out = None
            if wicket:
                dismissal_kind = wicket.get("kind"); player_out = wicket.get("player_out")
            elif wickets_list:
                wk = wickets_list[0]; dismissal_kind = wk.get("kind"); player_out = wk.get("player_out")
            extras = ball.get("extras", {}) or {}
            extras_type = next(iter(extras.keys())) if extras else None

            rows.append({
                "match_date": (dates_as_str_list(info) or [None])[0],
                "venue": info.get("venue"),
                "city": info.get("city"),
                "event": (info.get("event") or {}).get("name") if isinstance(info.get("event"), dict) else info.get("event"),
                "toss_winner": (info.get("toss") or {}).get("winner"),
                "toss_decision": (info.get("toss") or {}).get("decision"),
                "innings": innings_idx,
                "batting_team": batting_team,
                "over": over,
                "ball_in_over": ball_in_over,
                "striker": ball.get("batter"),
                "non_striker": ball.get("non_striker"),
                "bowler": ball.get("bowler"),
                "runs_batter": runs.get("batter", 0),
                "runs_extras": runs.get("extras", 0),
                "runs_total": runs.get("total", 0),
                "extras_type": extras_type,
                "wicket_event": wicket_event,
                "dismissal_kind": dismissal_kind,
                "player_out": player_out
            })
    return rows

def flatten_match_to_rows(match_json):
    info = match_json.get("info", {})
    all_rows = []
    innings_list = match_json.get("innings", [])
    for idx, innings_block in enumerate(innings_list, start=1):
        if isinstance(innings_block, dict) and "overs" in innings_block:
            all_rows.extend(rows_from_v2_innings(innings_block, info, idx))
        else:
            all_rows.extend(rows_from_legacy_innings(innings_block, info))
    return info, all_rows

def write_csv(rows, path):
    if not rows: return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", type=str, default="t20s_json.zip", help="Path to Cricsheet T20I zip")
    ap.add_argument("--jsondir", type=str, default=None, help="If provided, skip unzip and read JSONs from this dir")
    ap.add_argument("--outdir", type=str, default="outputs", help="Where to save CSVs")
    args = ap.parse_args()

    if args.jsondir:
        json_dir = Path(args.jsondir)
    else:
        json_dir = Path("data/t20s_json")
        json_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.zip, "r") as zf:
            zf.extractall(json_dir)

    found = {t["outfile"]: False for t in TARGETS}
    candidates_on_dates = {t["date"]: [] for t in TARGETS}

    for p in sorted(json_dir.glob("*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                match_json = json.load(f)
        except Exception:
            continue
        info, rows = flatten_match_to_rows(match_json)
        ds = dates_as_str_list(info)
        ev = norm_event_name(info.get("event"))
        teams = get_info_teams(info)

        for want_date in candidates_on_dates:
            if want_date in ds:
                candidates_on_dates[want_date].append((p.name, teams, ev))

        for T in TARGETS:
            if found[T["outfile"]]:
                continue
            strength = match_strength(info, T)
            if strength >= 2:
                write_csv(rows, os.path.join(args.outdir, T["outfile"]))
                found[T["outfile"]] = True

    # Fallback to date-only best
    for T in TARGETS:
        if found[T["outfile"]]:
            continue
        best = None
        for fname, teams, ev in candidates_on_dates.get(T["date"], []):
            if teams == T["teams"]:
                best = (fname, teams, ev); break
            if best is None:
                best = (fname, teams, ev)
        if best:
            with open(os.path.join(json_dir, best[0]), "r", encoding="utf-8") as f:
                match_json = json.load(f)
            _, rows = flatten_match_to_rows(match_json)
            write_csv(rows, os.path.join(args.outdir, T["outfile"]))

if __name__ == "__main__":
    main()
