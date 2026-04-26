"""
Ejemplo sencillo de likes. Credenciales: TINDER_EMAIL y TINDER_PASSWORD en el entorno.
Ver quickstart_tinder.py y quickstart_bumble.py para más opciones.
"""
import os
import sys

from core.error_reporting import run_with_error_report
from tinderbotz.session import Session
from tinderbotz.helpers.constants_helper import *


def main():
    session = Session()
    email = os.environ.get("TINDER_EMAIL", "").strip()
    password = os.environ.get("TINDER_PASSWORD", "").strip()
    if not email or not password:
        print("Define TINDER_EMAIL y TINDER_PASSWORD en el entorno.", file=sys.stderr)
        sys.exit(1)

    session.login_using_facebook(email, password)
    session.login_using_google(email, password)
    
    # spam likes
    # amount -> amount of people you want to like
    # ratio  -> chance of liking/disliking
    # sleep  -> amount of seconds to wait before swiping again
    session.like(amount=100, ratio="72.5%", sleep=1)


if __name__ == "__main__":
    run_with_error_report(main)
