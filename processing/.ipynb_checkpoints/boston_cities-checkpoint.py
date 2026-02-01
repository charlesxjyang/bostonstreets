import json

GREATER_BOSTON = {
    # Core
    "BOSTON", "CAMBRIDGE", "SOMERVILLE", "BROOKLINE", "CHELSEA",
    "REVERE", "EVERETT", "MALDEN", "MEDFORD", "WINTHROP",
    # # Inside 128/95
    # "ARLINGTON", "BELMONT", "WATERTOWN", "NEWTON", "NEEDHAM",
    # "DEDHAM", "MILTON", "QUINCY", "BRAINTREE", "RANDOLPH",
    # "CANTON", "NORWOOD", "WESTWOOD", "DOVER", "WELLESLEY",
    # "WESTON", "WALTHAM", "LEXINGTON", "WINCHESTER", "WOBURN",
    # "STONEHAM", "MELROSE", "WAKEFIELD", "SAUGUS", "LYNN"
}

import glob

input_files = glob.glob("data/*.geojson")
# Skip our output files
input_files = [f for f in input_files if "greater_boston" not in f and "duplicate" not in f]

output_file = "data/greater_boston.geojson"

kept = 0
total = 0

with open(output_file, "w") as fout:
    for input_file in input_files:
        print(f"Processing {input_file}...")
        with open(input_file, "r") as fin:
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                total += 1
                feature = json.loads(line)
                city = (feature.get("properties", {}).get("city") or "").strip().upper()
                if city in GREATER_BOSTON:
                    fout.write(json.dumps(feature) + "\n")
                    kept += 1

print(f"\nKept {kept} / {total} addresses from {len(input_files)} files")