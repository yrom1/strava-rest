import datetime
import json
import os
import subprocess
from textwrap import dedent
from zoneinfo import ZoneInfo

import pandas as pd
import requests
from cloud_dictionary import Cloud
from mypandas import MyPandas


def main():
    # TODO refresh token can change need to update it
    refresh = dedent(
        f"""curl -X POST https://www.strava.com/api/v3/oauth/token \
    -d client_id={os.environ['STRAVA_CLIENT_ID']} \
    -d client_secret={os.environ['STRAVA_CLIENT_SECRET']} \
    -d grant_type=refresh_token \
    -d refresh_token={os.environ['STRAVA_REFRESH_TOKEN']}"""
    )

    refresh_response = json.loads(
        subprocess.run(refresh, shell=True, capture_output=True).stdout.decode("utf-8")
    )
    access_token = refresh_response["access_token"]
    refresh_token = refresh_response["refresh_token"]

    # response = requests.post(
    #     url="https://www.strava.com/oauth/token",
    #     data={
    #         "client_id": os.environ["STRAVA_CLIENT_ID"],
    #         "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
    #         "code": os.environ["STRAVA_AUTH_CODE"],
    #         "grant_type": "authorization_code",
    #     },
    # )

    # with open("strava_tokens.json", "w") as f:
    #     json.dump(response.json(), f)

    # with open("strava_tokens.json") as f:
    #     strava_tokens = json.load(f)

    url = "https://www.strava.com/api/v3/activities"
    # access_token = strava_tokens["access_token"]
    r = requests.get(url + "?access_token=" + access_token)  # first page of activities
    r = r.json()

    df = pd.json_normalize(r)
    df = (
        df[df["type"] == "Run"][["distance", "start_date_local"]]
        .groupby(["start_date_local"], as_index=False)
        .sum()
    )  # distance is in meters

    df["start_date_local"] = pd.to_datetime(df["start_date_local"])
    # TODO this ignores daylight savings
    df["start_date_local"] = df["start_date_local"].dt.tz_convert("US/Eastern")
    dates_raw = [x.isoformat()[:10] for x in list(df["start_date_local"])]
    kms_raw = [round(x / 1000, 2) for x in list(df["distance"])]

    today = datetime.datetime.now(ZoneInfo("US/Eastern"))
    dates = [today - datetime.timedelta(days=x) for x in range(30)]
    dates_counter = {x.strftime("%Y-%m-%d"): 0 for x in dates}

    for i, date in enumerate(dates_raw):
        if date in dates_counter:
            dates_counter[date] += kms_raw[i]

    return list(dates_counter.keys()), list(dates_counter.values())


DATES, KMS = main()
print(DATES, KMS)
df = pd.DataFrame({"date": DATES, "kms": KMS})
query = """
SELECT SUM(kms)
FROM df
WHERE month(date) = month(now());
"""
Cloud("kpiV1")["KMS_RAN_THIS_MONTH"] = int(
    MyPandas("mysql://root:root@localhost")(query, locals()).values[0]
)
DATES, KMS = DATES[:14], KMS[:14]
