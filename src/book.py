import copy
from types import SimpleNamespace

import fire as fire

from utils import (
    check_and_book,
    display_info_dict,
    get_saved_user_info,
    reauthorize,
)


def main(filename):
    try:
        base_request_header = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/39.0.2171.95 Safari/537.36",
            # "x-api-key": "3sjOr2rmM52GzhpMHjDEE1kpQeRxwFDr4YcBEimi"
        }

        collected_details = get_saved_user_info(filename)
        display_info_dict(collected_details)

        while True:
            info = SimpleNamespace(**get_saved_user_info(filename))
            request_header = copy.deepcopy(base_request_header)
            request_header["Authorization"] = info.auth

            # call function to check and book slots
            if not check_and_book(
                request_header,
                info.beneficiary_dtls,
                info.location_dtls,
                preferred_slot=info.preferred_slot,
                min_slots=info.minimum_slots,
            ):
                print("Reauthorizing...")
                reauthorize(filename=filename)

    except Exception as e:
        print(str(e))
        print("Exiting Script")


if __name__ == "__main__":
    fire.Fire(main)
