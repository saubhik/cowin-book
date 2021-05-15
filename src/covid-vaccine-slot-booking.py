#!/usr/bin/env python3

import copy
from types import SimpleNamespace

import requests

from utils import (
    check_and_book,
    BENEFICIARIES_URL,
    display_info_dict,
    get_saved_user_info,
    reauthorize,
)


def main():
    filename = "config.json"

    try:
        base_request_header = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/39.0.2171.95 Safari/537.36",
        }

        collected_details = get_saved_user_info(filename)
        display_info_dict(collected_details)
        info = SimpleNamespace(**collected_details)

        while True:
            request_header = copy.deepcopy(base_request_header)
            request_header["Authorization"] = info.auth

            # call function to check and book slots
            check_and_book(
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
            beneficiaries_list = requests.get(BENEFICIARIES_URL, headers=request_header)
            if beneficiaries_list.status_code != 200:
                # if token invalid, regenerate OTP and new token
                print("Reauthorizing...")
                reauthorize()

    except Exception as e:
        print(str(e))
        print("Exiting Script")


if __name__ == "__main__":
    main()