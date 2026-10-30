
import csv
from pathlib import Path

path = Path(
    "/home/coco/RobAuditor/experiments/tracy_pick_place_phase1/"
    "scripts/output/randomized_pick_place_audit.csv"
)

if not path.exists():
    print(f"CSV file not found: {path}")
    raise SystemExit(1)

with path.open("r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    rows = list(reader)

if not rows:
    print("The CSV file is empty.")
    raise SystemExit(0)

print(f"\nTotal trials: {len(rows)}\n")

for row in rows:
    print(
        f"Trial {row.get('trial', '?')}: "
        f"reachable={row.get('reachable')}, "
        f"executed={row.get('executed')}, "
        f"workspace_rejected={row.get('workspace_rejected')}, "
        f"arm={row.get('selected_arm')}, "
        f"placement_success={row.get('placement_within_2cm')}, "
        f"recovery={row.get('recovery_strategy')}, "
        f"status={row.get('status')}"
    )

executed = sum(
    row.get("executed", "").strip().lower() in ("true", "1")
    for row in rows
)

rejected = sum(
    row.get("workspace_rejected", "").strip().lower() in ("true", "1")
    for row in rows
)

reachable = sum(
    row.get("reachable", "").strip().lower() in ("true", "1")
    for row in rows
)

successes = sum(
    row.get("placement_within_2cm", "").strip().lower() in ("true", "1")
    for row in rows
)

print("\n--- SUMMARY ---")
print(f"Total trials:        {len(rows)}")
print(f"Reachable trials:    {reachable}")
print(f"Executed trials:     {executed}")
print(f"Workspace rejected:  {rejected}")
print(f"Placement successes: {successes}")
