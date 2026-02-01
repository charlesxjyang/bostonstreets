import json
from collections import defaultdict
from math import radians, cos, sin, sqrt, atan2

def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3959
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

SUFFIX_MAP = {
    "STREET": "ST", "STREETS": "ST",
    "AVENUE": "AVE", "AV": "AVE",
    "BOULEVARD": "BLVD",
    "DRIVE": "DR",
    "ROAD": "RD",
    "LANE": "LN",
    "COURT": "CT",
    "PLACE": "PL",
    "CIRCLE": "CIR",
    "TERRACE": "TER", "TERR": "TER",
    "TRAIL": "TRL",
    "WAY": "WAY",
    "PARKWAY": "PKWY", "PKY": "PKWY",
    "HIGHWAY": "HWY",
    "SQUARE": "SQ",
    "CROSSING": "XING",
    "POINT": "PT",
    "LOOP": "LOOP",
    "PATH": "PATH",
    "PIKE": "PIKE",
    "TURNPIKE": "TPKE",
    "EXTENSION": "EXT",
    "ALLEY": "ALY",
    "COMMONS": "CMNS",
    "CRESCENT": "CRES",
    "HEIGHTS": "HTS",
    "HILL": "HL",
    "LANDING": "LNDG",
    "PARK": "PARK",
    "RIDGE": "RDG",
    "RUN": "RUN",
    "WALK": "WALK",
    "WHARF": "WHRF",
}

def normalize_street(street):
    parts = street.split()
    if not parts:
        return street
    last = parts[-1]
    if last in SUFFIX_MAP:
        parts[-1] = SUFFIX_MAP[last]
    return " ".join(parts)

MIN_DISTANCE_MILES = 0.4

input_file = "data/greater_boston.geojson"
output_file = "data/duplicate_addresses.json"

# Group by address + city
city_address_groups = defaultdict(list)

with open(input_file, "r") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        feature = json.loads(line)
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [None, None])

        number = (props.get("number") or "").strip().upper()
        street = (props.get("street") or "").strip().upper()
        city = (props.get("city") or "").strip().upper()
        postcode = (props.get("postcode") or "").strip()

        if not number or not street:
            continue

        street = normalize_street(street)
        key = f"{number} {street} | {city}"

        city_address_groups[key].append({
            "city": city,
            "postcode": postcode,
            "lon": coords[0],
            "lat": coords[1],
        })

# Manually add missing addresses
manual_entries = [
    {
        "number": "100",
        "street": "WASHINGTON ST",
        "city": "BOSTON",
        "postcode": "02109",
        "lon": -71.05779,
        "lat": 42.35899,
    },
]

for entry in manual_entries:
    key = f"{entry['number']} {entry['street']} | {entry['city']}"
    city_address_groups[key].append({
        "city": entry["city"],
        "postcode": entry["postcode"],
        "lon": entry["lon"],
        "lat": entry["lat"],
    })

# Dedupe: cluster by distance regardless of postcode
address_groups = defaultdict(list)

for key, locations in city_address_groups.items():
    address, city = key.rsplit(" | ", 1)

    # Cluster all locations by distance
    clusters = []
    for loc in locations:
        if loc["lat"] is None or loc["lon"] is None:
            continue
        placed = False
        for cluster in clusters:
            rep = cluster[0]
            if haversine_miles(rep["lat"], rep["lon"], loc["lat"], loc["lon"]) < MIN_DISTANCE_MILES:
                placed = True
                break
        if not placed:
            clusters.append([loc])

    for cluster in clusters:
        address_groups[address].append(cluster[0])

# Keep addresses with 2+ distinct locations
dupes = []
for address, locations in address_groups.items():
    if len(locations) >= 2:
        dupes.append({
            "address": address,
            "count": len(locations),
            "locations": [{
                "city": loc["city"],
                "postcode": loc["postcode"],
                "lon": round(loc["lon"], 4) if loc["lon"] is not None else None,
                "lat": round(loc["lat"], 4) if loc["lat"] is not None else None,
            } for loc in locations],
        })

dupes.sort(key=lambda x: x["count"], reverse=True)

output = {
    "total": len(dupes),
    "duplicates": dupes,
}

with open(output_file, "w") as f:
    json.dump(output, f, separators=(',', ':'))

import os
size_mb = os.path.getsize(output_file) / 1024 / 1024
print(f"Saved {len(dupes)} duplicate addresses to {output_file} ({size_mb:.1f} MB)")

print(f"\nTop 20:")
for d in dupes[:20]:
    cities = [f"{loc['city']} {loc['postcode']}" for loc in d["locations"]]
    print(f"  {d['address']} — {d['count']} locations: {', '.join(cities)}")
