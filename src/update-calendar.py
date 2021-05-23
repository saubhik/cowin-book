# python src/update-calendar.py --location-config location-config.json
import json
import time
from datetime import datetime, timedelta

import fire
import requests

# This does NOT require auth.
CALENDAR_URL_DISTRICT = (
    "https://cdn-api.co-vin.in/api/v2/appointment"
    "/sessions/public/calendarByDistrict?district_id={0}&date={1} "
)


def main(location_config: str) -> None:
    while True:
        # Start checking available slots from next day.
        start_date = (datetime.today() + timedelta(days=1)).strftime("%d-%m-%Y")

        with open(file=location_config, mode="r") as f:
            config = json.load(f)

        for location in config["location_dtls"]:
            resp = requests.get(
                CALENDAR_URL_DISTRICT.format(location["district_id"], start_date),
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/39.0.2171.95 Safari/537.36"
                },
            )

            if resp.status_code == 403:
                # Encountered rate limit.
                print("403: Sleeping 60 seconds...")
                time.sleep(60)

            elif resp.status_code == 200:
                resp = resp.json()
                timestamp = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                if "centers" in resp:
                    print(
                        f"Centers available in {location['district_name']} "
                        f"from {start_date} as of "
                        f"{timestamp}: "
                        f"{len(resp['centers'])}"
                    )
                resp["timestamp"] = timestamp
                with open(
                    file=f"calendar-{location['district_id']}.json", mode="w"
                ) as f:
                    json.dump(resp, f)

            time.sleep(2)


if __name__ == "__main__":
    fire.Fire(main)
