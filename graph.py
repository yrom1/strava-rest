import pandas as pd
from cloud_dictionary import Cloud

from main import DATES, KMS
from stardb import StarSchema

if __name__ == "__main__":
    DAYS_SINCE_LAST_RUN: str
    for i, distance in enumerate(KMS):
        if distance > 0:
            DAYS_SINCE_LAST_RUN = i
            break
    else:
        DAYS_SINCE_LAST_RUN = 14

    Cloud("kpiV1")["DAYS_SINCE_LAST_RUN"] = DAYS_SINCE_LAST_RUN

    DATES, KMS = DATES[::-1], KMS[::-1]

    df = pd.DataFrame({"date": DATES, "value": KMS})
    df.to_json("plot.json")
    with open("plot.json", "r") as f:
        Cloud("plotsV2")["strava"] = f.read()

    with StarSchema() as rds:
        rds.insert_dimension("dimension_strava", [KMS[0]])
