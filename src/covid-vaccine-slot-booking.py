#!/usr/bin/env python3

import argparse
import copy
from types import SimpleNamespace

import requests

from utils import (
    generate_token_OTP,
    check_and_book,
    BENEFICIARIES_URL,
    display_info_dict,
    get_saved_user_info,
    send_email
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", help="Pass token directly")
    args = parser.parse_args()

    filename = "vaccine-booking-details.json"
    mobile = 9051132578

    try:
        base_request_header = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/39.0.2171.95 Safari/537.36",
        }

        if args.token:
            token = args.token
        else:
            token = generate_token_OTP(mobile, base_request_header)

        request_header = copy.deepcopy(base_request_header)
        request_header["Authorization"] = f"Bearer {token}"

        collected_details = get_saved_user_info(filename)
        display_info_dict(collected_details)
        info = SimpleNamespace(**collected_details)

        token_valid = True
        while token_valid:
            request_header = copy.deepcopy(base_request_header)
            request_header["Authorization"] = f"Bearer {token}"

            # call function to check and book slots
            token_valid = check_and_book(
                request_header,
                info.beneficiary_dtls,
                info.location_dtls,
                min_slots=info.minimum_slots,
                ref_freq=info.refresh_freq,
                auto_book=info.auto_book,
                start_date=info.start_date,
                vaccine_type=info.vaccine_type,
                fee_type=info.fee_type,
            )

            # check if token is still valid
            beneficiaries_list = requests.get(BENEFICIARIES_URL,
                                              headers=request_header)
            if beneficiaries_list.status_code == 200:
                token_valid = True

            else:
                # if token invalid, regenerate OTP and new token
                send_email()
                print("Token is INVALID.")
                token_valid = False

                tryOTP = input("Try for a new Token? (y/n Default y): ")
                if tryOTP.lower() == "y" or not tryOTP:
                    token = generate_token_OTP(mobile, base_request_header)
                    token_valid = True
                else:
                    print("Exiting")

    except Exception as e:
        print(str(e))
        print("Exiting Script")


if __name__ == "__main__":
    main()
