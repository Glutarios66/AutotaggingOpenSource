import opendataloader_pdf
import json
import sys

filepath = sys.argv[1]  # pass your PDF as argument

opendataloader_pdf.convert(
    input_path=[filepath],
    output_dir="output/inspect/",
    format="json"
)

# Read the output JSON and print it cleanly
import os
output_file = f"output/inspect/{os.path.splitext(os.path.basename(filepath))[0]}.json"

with open(output_file, "r") as f:
    data = json.load(f)

with open(output_file, "r") as f:
    data = json.load(f)

for element in data.get("elements", []):
    print(
        f"[Page {element.get('page', '?')}] "
        f"{element.get('type', '?').upper()}: "
        f"{str(element.get('text', ''))[:80]}"
    )