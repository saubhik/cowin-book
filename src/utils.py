import copy
import datetime
import json
import subprocess
import sys
import time

import requests
import tabulate

from captcha import captcha_buider

BOOKING_URL = "https://cdn-api.co-vin.in/api/v2/appointment/schedule"
CAPTCHA_URL = "https://cdn-api.co-vin.in/api/v2/auth/getRecaptcha"


def reauthorize(config):
    subprocess.run(["node", "src/get-token.js", config])


def viable_options(resp, minimum_slots, min_age_booking):
    options = []
    display_options = []
    if len(resp["centers"]) >= 0:
        for center in resp["centers"]:
            can_display = False
            total_available_capacity = 0
            for session in center["sessions"]:
                if (
                    (min_age_booking >= 45 and session["min_age_limit"] == 45)
                    or (45 > min_age_booking >= 18 and session["min_age_limit"] == 18)
                    # and session["fee_type"] == "Paid"
                    and session["vaccine"] == "COVISHIELD"
                ):
                    can_display = True
                    total_available_capacity += session["available_capacity"]
                    if session["available_capacity"] >= minimum_slots:
                        out = {
                            "name": center["name"],
                            "district": center["district_name"],
                            "pincode": center["pincode"],
                            "center_id": center["center_id"],
                            "available": session["available_capacity"],
                            "date": session["date"],
                            "slots": session["slots"],
                            "session_id": session["session_id"],
                        }
                        options.append(out)

            if can_display:
                display_options.append(
                    {
                        "timestamp": resp["timestamp"],
                        "name": center["name"],
                        "available": total_available_capacity,
                    }
                )

    display_table(display_options)

    return options


def display_table(dict_list):
    """
    This function
        1. Takes a list of dictionary
        2. Add an Index column, and
        3. Displays the data in tabular format
    """
    if dict_list:
        header = ["idx"] + list(dict_list[0].keys())
        rows = [[idx + 1] + list(x.values()) for idx, x in enumerate(dict_list)]
        print(tabulate.tabulate(rows, header, tablefmt="grid"))


def display_info_dict(details):
    for key, value in details.items():
        if isinstance(value, list):
            if all(isinstance(item, dict) for item in value):
                print(f"\t{key}:")
                display_table(value)
            else:
                print(f"\t{key}\t: {value}")
        else:
            print(f"\t{key}\t: {value}")


def get_saved_user_info(filename):
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def generate_captcha(request_header, api_key):
    print(
        "================================= GETTING CAPTCHA "
        "=================================================="
    )
    resp = requests.post(CAPTCHA_URL, headers=request_header)
    print(f"CAPTCHA Response Code: {resp.status_code}")

    if resp.status_code == 200:
        captcha = captcha_buider(resp.json(), api_key)
        return captcha


def book_appointment(request_header, details, api_key):
    """
    This function
        1. Takes details in json format
        2. Attempts to book an appointment using the details
        3. Returns True or False depending on Token Validity
    """
    try:
        # Requires VLC to be installed.
        # Might need to change to cvlc in Linux.
        subprocess.Popen(
            ["vlc", "-I", "rc", "src/siren.mp3"],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        valid_captcha = True
        while valid_captcha:
            captcha = generate_captcha(request_header, api_key)
            details["captcha"] = captcha

            print(
                "================================= ATTEMPTING BOOKING "
                "=================================================="
            )

            resp = requests.post(BOOKING_URL, headers=request_header, json=details)
            print(f"Booking Response Code: {resp.status_code}")
            print(f"Booking Response : {resp.text}")

            if resp.status_code == 401:
                return False
            elif resp.status_code == 200:
                print("It's your lucky day!")
                sys.exit()
            elif resp.status_code == 400:
                print(f"Response: {resp.status_code} : {resp.text}")
                pass
            elif resp.status_code == 409:
                sys.exit()
            else:
                print(f"Response: {resp.status_code} : {resp.text}")
                return True

    except Exception as e:
        print(str(e))


def check_and_book(request_header, beneficiary_dtls, location_dtls, **kwargs):
    """
    This function
        1. Checks the vaccination calendar for available slots,
        2. Lists all viable options,
        3. Takes user's choice of vaccination center and slot,
        4. Calls function to book appointment, and
        5. Returns True or False depending on Token Validity
    """
    min_age_booking = get_min_age(beneficiary_dtls)

    preferred_slot = kwargs["preferred_slot"]
    minimum_slots = kwargs["min_slots"]
    api_key = kwargs["api_key"]

    # Start checking available slots from next day.
    start_date = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime(
        "%d-%m-%Y"
    )

    options = []
    for location in location_dtls:
        with open(file=f"calendar-{location['district_id']}.json", mode="r") as f:
            resp = json.load(f)
        options += viable_options(resp, minimum_slots, min_age_booking)

    options = sorted(
        options,
        key=lambda k: (
            k["district"].lower(),
            k["pincode"],
            k["name"].lower(),
            datetime.datetime.strptime(k["date"], "%d-%m-%Y"),
        ),
    )

    tmp_options = copy.deepcopy(options)
    if len(tmp_options) > 0:
        cleaned_options_for_display = []
        for item in tmp_options:
            item.pop("session_id", None)
            item.pop("center_id", None)
            cleaned_options_for_display.append(item)

        display_table(cleaned_options_for_display)
        print(
            "AUTO-BOOKING IS ENABLED. PROCEEDING WITH FIRST CENTRE, "
            "DATE, and PREFERRED SLOT."
        )
        choice = f"1.{preferred_slot}"
    else:
        for i in range(3, 0, -1):
            msg = f"No viable options. Next update in {i} seconds.."
            print(msg, end="\r", flush=True)
            sys.stdout.flush()
            time.sleep(1)
        choice = "."

    if choice == ".":
        return True
    else:
        try:
            choice = choice.split(".")
            choice = [int(item) for item in choice]
            print(
                f"============> Got Choice: Center #{choice[0]}, " f"Slot #{choice[1]}"
            )

            new_req = {
                "beneficiaries": [
                    beneficiary["bref_id"] for beneficiary in beneficiary_dtls
                ],
                "dose": 2
                if [beneficiary["status"] for beneficiary in beneficiary_dtls][0]
                == "Partially Vaccinated"
                else 1,
                "center_id": options[choice[0] - 1]["center_id"],
                "session_id": options[choice[0] - 1]["session_id"],
                "slot": options[choice[0] - 1]["slots"][choice[1] - 1],
            }

            print(f"Booking with info: {new_req}")
            return book_appointment(request_header, new_req, api_key)

        except IndexError:
            print("============> Invalid Option!")
            sys.exit()


def get_min_age(beneficiary_dtls):
    """
    This function returns a min age argument, based on age of all beneficiaries
    :param beneficiary_dtls:
    :return: min_age:int
    """
    age_list = [item["age"] for item in beneficiary_dtls]
    min_age = min(age_list)
    return min_age
