"""
Bumble quickstart: like con BumbleSession.
Run from project root: python quickstart_bumble.py

Opcional: BUMBLE_SMS_COUNTRY y BUMBLE_SMS_PHONE para login por SMS automático.
Sin ellas se usa la sesión en chrome_profile_bumble/; se abre /app y se espera la redirección automáticamente.
"""
import atexit
import os
import sys

from core.error_reporting import run_with_error_report
from bumblebotz import Session

AMOUNT = 500
RATIO = "95%"
SLEEP = 4

def main():
    session = Session()
    # session = Session(proxy="user:pass@host:port")  # opcional

    country = os.environ.get("BUMBLE_SMS_COUNTRY", "").strip()
    phone = os.environ.get("BUMBLE_SMS_PHONE", "").strip()
    if country and phone:
        session.login_using_sms(country, phone)
        if not session.is_logged_in():
            print("No se pudo iniciar sesión. Revisa número y código SMS.")
            return
    if not session.is_logged_in():
        print("No hay sesión activa en Bumble.", file=sys.stderr)
        return

    session.like(amount=AMOUNT, ratio=RATIO, sleep=SLEEP, reject_if_male=True)
    print("Bumble quickstart hecho. Cierra el navegador cuando termines.")

if __name__ == "__main__":
    atexit.register(lambda: print("Sesión finalizada."))
    run_with_error_report(main)
