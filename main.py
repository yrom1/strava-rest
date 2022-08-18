import datetime
import json
import os

import pandas as pd
import requests


url = f'http://www.strava.com/oauth/authorize?client_id={os.environ["STRAVA_CLIENT_ID"]}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all'
print(url)


def main():
    response = requests.post(
        url="https://www.strava.com/oauth/token",
        data={
            "client_id": os.environ["STRAVA_CLIENT_ID"],
            "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
            "code": os.environ["STRAVA_AUTH_CODE"],
            "grant_type": "authorization_code",
        },
    )

    with open("strava_tokens.json", "w") as f:
        json.dump(response.json(), f)

    with open("strava_tokens.json") as f:
        strava_tokens = json.load(f)

    url = "https://www.strava.com/api/v3/activities"
    access_token = strava_tokens["access_token"]
    r = requests.get(url + "?access_token=" + access_token)  # first page of activities
    r = r.json()

    df = pd.json_normalize(r)
    df = pd.read_pickle("test")
    df = df[df["type"] == "Run"]
    df = df[["start_date_local", "distance"]]  # distance is in meters
    df = df.groupby(["start_date_local"]).sum()
    df["start_date_local"] = df.index

    # TODO better way to do this?
    """
    >>> df['start_date_local'] = df.index
    >>> df
                        distance      start_date_local
    start_date_local
    2022-08-18T11:05:11Z     249.9  2022-08-18T11:05:11Z
    """

    dates_raw = [x[:10] for x in list(df["start_date_local"])]
    kms_raw = [round(x / 1000, 2) for x in list(df["distance"])]

    today = datetime.datetime.today()
    dates = [today - datetime.timedelta(days=x) for x in range(14)]
    # TODO whats the actual function in datetime for this?
    dates_counter = {
        f"{x.year}-{str(x.month).zfill(2)}-{str(x.day).zfill(2)}": 0 for x in dates
    }

    for i, date in enumerate(dates_raw):
        if date in dates_counter:
            dates_counter[date] += kms_raw[i]

    return list(dates_counter.keys()), list(dates_counter.values())


DATES, KMS = main()
