# python src/reauthorize.py "['config1.json','config2.json','config3.json']"
import sys
import time
from datetime import datetime
from typing import List

import fire

from utils import reauthorize


def main(configs: List[str]) -> None:
    while True:
        for config in configs:
            print(
                f"Reauthorizing {config} at "
                f"{datetime.today().strftime('%Y-%m-%d %H:%M:%S')}..."
            )
            reauthorize(config)
            time.sleep(3)

        # Do this every 14 minutes.
        for i in range(14 * 60, 0, -1):
            msg = f"Reauthorizing in {i} seconds.."
            print(msg, end="\r", flush=True)
            sys.stdout.flush()
            time.sleep(1)


if __name__ == "__main__":
    fire.Fire(main)
