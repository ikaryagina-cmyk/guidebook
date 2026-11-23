#!/usr/bin/env python3
"""Download approved public schedule fields from Apps Script."""
import json
import os
import re
import urllib.request
from pathlib import Path

endpoint = os.environ["SCHEDULE_ENDPOINT"]
url = endpoint + ("&" if "?" in endpoint else "?") + "callback=GamesScheduleReceive"
request = urllib.request.Request(url, headers={"User-Agent": "guidebook-schedule-sync/1.0"})
with urllib.request.urlopen(request, timeout=180) as response:
    content = response.read(10_000_000).decode("utf-8-sig")
match = re.fullmatch(r"\s*GamesScheduleReceive\((\{.*\})\);?\s*", content, re.S)
if not match:
    raise RuntimeError("Unexpected response from schedule endpoint")
data = json.loads(match.group(1))
if not isinstance(data.get("rows"), list) or len(data["rows"]) < 100:
    raise RuntimeError("Missing or unexpectedly small schedule: refusing to overwrite")
allowed = ("group", "date", "name", "rating", "score", "guide")
rows = []
for item in data["rows"]:
    if not isinstance(item, dict) or item.get("group") not in ("current", "archive", "special"):
        raise RuntimeError("Invalid row")
    rows.append({key: str(item.get(key) or "") for key in allowed})
out = {"updatedAt": data.get("updatedAt"), "rows": rows}
Path("games-schedule-data.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
print("Validated", len(rows), "rows")
