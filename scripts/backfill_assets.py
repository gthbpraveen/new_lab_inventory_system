
# scripts/backfill_assets.py
# scripts/backfill_assets.py
"""
Safe backfill script for workstation_asset *_new columns.
Usage (from project root):
    python3 scripts/backfill_assets.py
"""
import os
import sys
import re
from datetime import datetime

# Ensure project root is on sys.path so "models" and "app" import work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# now imports should succeed
from models import db, WorkstationAsset

# Try to import app object from app.py (you use FLASK_APP=app.py)
try:
    # prefer 'app' exported directly in app.py
    from app import app
except Exception:
    # fallback: try a create_app factory if present
    try:
        from app import create_app
        app = create_app()
    except Exception as e:
        raise SystemExit("Could not import Flask app from app.py. Edit this script to import your app. Error: " + str(e))

def parse_first_int(s):
    if s is None:
        return None
    m = re.search(r'(\d+)', str(s))
    return int(m.group(1)) if m else None

def parse_date_try_formats(s):
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    return None

def backfill():
    with app.app_context():
        assets = WorkstationAsset.query.all()
        print(f"Backfilling {len(assets)} assets...")
        updated = 0
        for a in assets:
            changed = False

            # cores -> cores_new
            if getattr(a, 'cores', None) is not None:
                val = parse_first_int(a.cores)
                if val is not None:
                    a.cores_new = val
                else:
                    a.cores_new = None
                changed = True

            # vram -> vram_new
            if getattr(a, 'vram', None) is not None:
                a.vram_new = parse_first_int(a.vram)
                changed = True

            # storage capacities
            if getattr(a, 'storage_capacity1', None) is not None:
                a.storage_capacity1_new = parse_first_int(a.storage_capacity1)
                changed = True
            if getattr(a, 'storage_capacity2', None) is not None:
                a.storage_capacity2_new = parse_first_int(a.storage_capacity2)
                changed = True

            # dates -> try parse
            if getattr(a, 'po_date', None):
                a.po_date_new = parse_date_try_formats(a.po_date)
                changed = True
            if getattr(a, 'warranty_start', None):
                a.warranty_start_new = parse_date_try_formats(a.warranty_start)
                changed = True
            if getattr(a, 'warranty_expiry', None):
                a.warranty_expiry_new = parse_date_try_formats(a.warranty_expiry)
                changed = True

            if changed:
                db.session.add(a)
                updated += 1

        db.session.commit()
        print(f"Backfill complete. Updated {updated} rows.")

if __name__ == "__main__":
    backfill()

