# from app import app, db
# from models import WorkstationAsset

# with app.app_context():
#     # Fetch assets where department_code is null or empty
#     assets = WorkstationAsset.query.filter(
#         (WorkstationAsset.department_code == None) | 
#         (WorkstationAsset.department_code == "")
#     ).all()

#     for idx, asset in enumerate(assets, start=1):
#         # Clean PO date
#         po_date_raw = asset.po_date or "Unknown"
#         po_date = po_date_raw.replace("-", "")

#         # Clean indenter (remove Dr./Prof. and take only first name)
#         indenter_full = asset.indenter or "Unknown"
#         indenter_clean = indenter_full.replace("Dr. ", "").replace("Prof. ", "").replace("M.V.Panduranga Rao","MVP")
#         indenter_first = indenter_clean.split()[0]

#         # Manufacturer + model
#         manufacturer = asset.manufacturer or "Unknown"
#         model = asset.model or "Unknown"

#         # Sequential number
#         serial = f"{idx:03}"

#         # Construct department_code
#         asset.department_code = f"CSE/{po_date}/{manufacturer}/{model}/{indenter_first}/{serial}"

#     # Save updates
#     db.session.commit()
#     print(f"✅ Updated {len(assets)} assets with department codes.")
from app import app, db
from models import Equipment

with app.app_context():
    # Fetch equipment where department_code is null or empty
    items = Equipment.query.filter(
        (Equipment.department_code == None) |
        (Equipment.department_code == "")
    ).all()

    # Dictionary to track category-wise serials
    category_counters = {}

    for item in items:
        # Clean PO date
        po_date_raw = item.po_date or "Unknown"
        po_date = po_date_raw.replace("-", "")

        # Clean indenter (remove Dr./Prof. and take only first name)
        indenter_full = item.intender_name or "Unknown"
        indenter_clean = (
            indenter_full.replace("Dr. ", "")
                         .replace("Prof. ", "")
                         .replace("M.V.Panduranga Rao", "MVP")
        )
        indenter_first = indenter_clean.split()[0]

        # Category + Manufacturer
        category = item.category or "Unknown"
        manufacturer = item.manufacturer or "Unknown"

        # Increment category counter
        if category not in category_counters:
            category_counters[category] = 1
        else:
            category_counters[category] += 1

        # Serial (category-wise)
        serial = f"{category_counters[category]:03}"

        # Construct department_code
        item.department_code = f"CSE/{po_date}/{category}/{manufacturer}/{indenter_first}/{serial}"

    # Save updates
    db.session.commit()
    print(f"✅ Updated {len(items)} equipment records with department codes (category-wise serials).")
