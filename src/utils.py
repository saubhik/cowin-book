import copy
import datetime
import json
import os
import subprocess
import sys
import time

import requests
import tabulate

from captcha import captcha_buider

BOOKING_URL = "https://cdn-api.co-vin.in/api/v2/appointment/schedule"
BENEFICIARIES_URL = "https://cdn-api.co-vin.in/api/v2/appointment/beneficiaries"
CALENDAR_URL_DISTRICT = (
    "https://cdn-api.co-vin.in/api/v2/appointment"
    "/sessions/calendarByDistrict?district_id={0}&date={1} "
)
CAPTCHA_URL = "https://cdn-api.co-vin.in/api/v2/auth/getRecaptcha"


def reauthorize():
    subprocess.run(["node", "src/get-token.js"])


def viable_options(resp, minimum_slots, min_age_booking, fee_type):
    options = []
    display_options = []
    if len(resp["centers"]) >= 0:
        for center in resp["centers"]:
            can_display = False
            total_available_capacity = 0
            for session in center["sessions"]:
                if (session["min_age_limit"] <= min_age_booking) and (
                    center["fee_type"] in fee_type
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
                        "name": center["name"],
                        "district": center["district_name"],
                        "pincode": center["pincode"],
                        "capacity": total_available_capacity,
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


def check_calendar_by_district(
    request_header,
    location_dtls,
    start_date,
    minimum_slots,
    min_age_booking,
    fee_type,
):
    """
    This function
        1. Takes details required to check vaccination calendar
        2. Filters result by minimum number of slots available
        3. Returns False if token is invalid
        4. Returns list of vaccination centers & slots if available
    """
    try:
        today = datetime.datetime.today()
        base_url = CALENDAR_URL_DISTRICT

        options = []
        for location in location_dtls:
            resp = requests.get(
                base_url.format(location["district_id"], start_date),
                headers=request_header,
            )

            if resp.status_code == 401:
                print("TOKEN INVALID")
                return False

            elif resp.status_code == 200:
                resp = resp.json()
                if "centers" in resp:
                    print(
                        f"Centers available in {location['district_name']} "
                        f"from {start_date} as of "
                        f"{today.strftime('%Y-%m-%d %H:%M:%S')}: "
                        f"{len(resp['centers'])}"
                    )
                    options += viable_options(
                        resp, minimum_slots, min_age_booking, fee_type
                    )

        return options

    except Exception as e:
        print(str(e))


def generate_captcha(request_header):
    print(
        "================================= GETTING CAPTCHA "
        "=================================================="
    )
    resp = requests.post(CAPTCHA_URL, headers=request_header)
    print(f"CAPTCHA Response Code: {resp.status_code}")

    if resp.status_code == 200:
        captcha = captcha_buider(resp.json())
        return captcha


def book_appointment(request_header, details):
    """
    This function
        1. Takes details in json format
        2. Attempts to book an appointment using the details
        3. Returns True or False depending on Token Validity
    """
    try:
        subprocess.Popen(["cvlc", "src/siren.mp3"])
        valid_captcha = True
        while valid_captcha:
            captcha = generate_captcha(request_header)
            details["captcha"] = captcha

            print(
                "================================= ATTEMPTING BOOKING "
                "=================================================="
            )

            resp = requests.post(BOOKING_URL, headers=request_header, json=details)
            print(f"Booking Response Code: {resp.status_code}")
            print(f"Booking Response : {resp.text}")

            if resp.status_code == 401:
                print("TOKEN INVALID")
                return False

            elif resp.status_code == 200:
                print("Hey, Hey, Hey! It's your lucky day!")
                print("\nPress any key thrice to exit program.")
                os.system("pause")
                os.system("pause")
                os.system("pause")
                sys.exit()

            elif resp.status_code == 400:
                print(f"Response: {resp.status_code} : {resp.text}")
                pass

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

    minimum_slots = kwargs["min_slots"]
    fee_type = kwargs["fee_type"]

    start_date = datetime.datetime.today().strftime("%d-%m-%Y")

    options = check_calendar_by_district(
        request_header,
        location_dtls,
        start_date,
        minimum_slots,
        min_age_booking,
        fee_type,
    )

    if isinstance(options, bool):
        return False

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
            "DATE, and FIRST SLOT."
        )
        # option = options[0]
        # random_slot = random.randint(1, len(option["slots"]))
        slot = 1
        choice = f"1.{slot}"

    else:
        for i in range(5, 0, -1):
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
            return book_appointment(request_header, new_req)

        except IndexError:
            print("============> Invalid Option!")


def get_min_age(beneficiary_dtls):
    """
    This function returns a min age argument, based on age of all beneficiaries
    :param beneficiary_dtls:
    :return: min_age:int
    """
    age_list = [item["age"] for item in beneficiary_dtls]
    min_age = min(age_list)
    return min_age
