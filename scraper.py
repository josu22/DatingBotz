"""
Scraper de geomatches. Credenciales: TINDER_EMAIL y TINDER_PASSWORD en el entorno.
"""
import os
import random
import sys
import time

from core.error_reporting import run_with_error_report
from tinderbotz.session import Session


def main():
    session = Session()

    session.set_custom_location(latitude=50.879829, longitude=4.700540)

    email = os.environ.get("TINDER_EMAIL", "").strip()
    password = os.environ.get("TINDER_PASSWORD", "").strip()
    if not email or not password:
        print("Define TINDER_EMAIL y TINDER_PASSWORD en el entorno.", file=sys.stderr)
        sys.exit(1)

    session.login_using_facebook(email, password)

    while True:
        geomatch = session.get_geomatch(quickload=False)

        if geomatch is None:
            try:
                session.browser.refresh()
            except Exception:
                pass
            time.sleep(random.random() * 4)
            continue

        if geomatch.get_name() is not None and geomatch.get_image_urls() != []:
            session.store_local(geomatch)
            print(geomatch.get_dictionary())
            session.dislike()
        else:
            session.browser.refresh()

        sleepy_time = random.random() * 4
        time.sleep(sleepy_time)


if __name__ == "__main__":
    run_with_error_report(main)
