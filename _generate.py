import math

import pandas as pd
import os
import sys
import shutil
import requests
import yaml
import json
from math import ceil

template = """---
layout: object
iden: {iden}
---
"""


def fix(value):
    if value != value:
        return ""
    elif isinstance(value, int):
        return value
    elif '"' in value:
        return value.replace('"', "'")
    return value


if __name__ == "__main__":
    shutil.rmtree("objects", ignore_errors=True)
    os.makedirs("objects")

    df_data = pd.read_csv("_data/data.csv")

    manifest_data = {}

    for index, row in df_data.iterrows():
        if row["Access"] == "access_public":
            manifest_url = row["PURL"].replace("/r/", "/iiif/") + "/manifest"
            manifest = requests.get(manifest_url).json()

            with open("test.json", "w+") as f:
                json.dump(manifest, f, indent=4)

            thumbnail = manifest["thumbnail"][0]["id"]

            # Get annotations
            annotations = []
            annotation_data = manifest["items"][0]["annotations"]
            if len(annotation_data) > 0:
                for annot in annotation_data[0]["items"]:
                    time = annot["target"].split("=")[-1].split(",")

                    secs = float(time[0])

                    hours = int(secs // 3600)
                    minutes = int(secs // 60)
                    seconds = int(secs % 60)

                    annotations.append({
                        "value": annot["body"][0]["value"],
                        "time": secs,
                        "formatted": f"({hours:02}:{minutes:02}:{seconds:02})"
                    })

            stream_link = manifest["items"][0]["items"][0]["items"][0]["body"]["id"]

            # Metadata
            metadata = []
            for meta in manifest["metadata"]:
                metadata.append({
                    "key": meta["label"]["en"][0],
                    "value": meta["value"]["en"][0],
                })

            # Duration
            hours = int(manifest["items"][0]["duration"] // 3600)
            duration = manifest["items"][0]["duration"]

            manifest_data[row["aviary ID"]] = {
                "thumbnail": thumbnail,
                "medium": thumbnail.replace("small", "medium"),
                "annotations": annotations,
                "metadata": metadata,
                "seconds": duration,
                "date": row["Date"],
                "title": row["Title"],
                "stream": stream_link.split("?")[0],
            }

            new = template.format(
                iden=fix(row["aviary ID"]),
            )

            with open(f"objects/{row['aviary ID']}.md", "w+") as f:
                print(new, file=f)

    # Create main data index
    with open("_data/objects.yml", "w+") as f:
        yaml.dump(manifest_data, f)

    objects_index = []
    for name, entry in manifest_data.items():
        objects_index.append({
            "iden": name,
            "title": entry["title"],
            "thumbnail": entry["thumbnail"],
            "date": entry["date"] if entry["date"] == entry["date"] else None,
            "lunr_id": len(objects_index),
            "permalink": f"/objects/{name}",
            **{i["key"]: i["value"] for i in entry["metadata"]}
        })

    # Create objects search index.
    with open("search/objects.json", "w+") as f:
        print("---", file=f)
        print("layout: none", file=f)
        print("---", file=f)
        print(json.dumps(objects_index, indent=4), file=f)
