"""
Tinder quickstart – uses tinderbotz.Session.
Run from project root: python quickstart_tinder.py

Opcional: TINDER_EMAIL y TINDER_PASSWORD para login automático.
Sin ellas se usa la sesión en chrome_profile_tinder/; si no hay sesión, inicia sesión en el navegador y pulsa ENTER.
"""
import atexit
import os
import sys

from core.error_reporting import run_with_error_report
from tinderbotz.session import Session
from tinderbotz.helpers.constants_helper import *

def main():
    session = Session()
    email = os.environ.get("TINDER_EMAIL", "").strip()
    password = os.environ.get("TINDER_PASSWORD", "").strip()
    if email and password:
        session.login_using_google(email, password)
    elif not session.is_logged_in():
        print(
            "Sin credenciales en el entorno: inicia sesión en Tinder en el navegador (perfil persistente) y pulsa ENTER.",
            file=sys.stderr,
        )
        input()
    if not session.is_logged_in():
        print("No hay sesión activa en Tinder.", file=sys.stderr)
        return
    # session.login_using_facebook(email, password)
    # session.login_using_sms(os.environ.get("TINDER_SMS_COUNTRY", ""), os.environ.get("TINDER_SMS_PHONE", ""))

    # Dar likes en la sección principal (recomendaciones)
    session.like(amount=500, ratio="97.5%", sleep=2, reject_if_male=True, save_liked_photos=True)
    # Ir a otra sección (explore u otra) y dar likes ahí también:
    # session.navigate_to("explore")   # o "explore/events", "explore/***", etc.
    # session.like(amount=20)
    session.dislike(amount=1)
    session.set_distance_range(km=60)
    session.set_age_range(18, 35)
    session.set_sexuality(Sexuality.WOMEN)
    session.set_global(True)

    new_matches = session.get_new_matches(amount=10, quickload=False)
    for match in new_matches:
        session.store_local(match)
        name, id = match.get_name(), match.get_chat_id()
        session.send_message(chatid=id, message="Hey {}! You. Me. Pizza?".format(name))

    for _ in range(5):
        geomatch = session.get_geomatch(quickload=False)
        if geomatch:
            session.store_local(geomatch)
        session.dislike()

if __name__ == "__main__":
    atexit.register(lambda: print("Sesión finalizada."))
    run_with_error_report(main)
