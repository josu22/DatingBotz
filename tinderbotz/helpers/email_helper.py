import os
import smtplib
from email.message import EmailMessage


class EmailHelper:
    """
    Envío de correo vía SMTP (Gmail u otro). No hay credenciales en el código:
    define en el entorno TINDERBOTZ_SMTP_USER, TINDERBOTZ_SMTP_PASSWORD y opcionalmente
    TINDERBOTZ_SMTP_FROM (por defecto igual que USER).
    """

    @staticmethod
    def send_mail_match_found(to):
        user = os.environ.get("TINDERBOTZ_SMTP_USER", "").strip()
        password = os.environ.get("TINDERBOTZ_SMTP_PASSWORD", "").strip()
        from_addr = os.environ.get("TINDERBOTZ_SMTP_FROM", user).strip() or user
        if not user or not password:
            raise RuntimeError(
                "Correo deshabilitado: define TINDERBOTZ_SMTP_USER y TINDERBOTZ_SMTP_PASSWORD."
            )

        match_msg = (
            "Congratulations you've been matched with someone. "
            "Please check your profile for more details."
        )
        msg = EmailMessage()
        msg.set_content(match_msg)
        msg["Subject"] = "NEW TINDER MATCH"
        msg["From"] = from_addr
        msg["To"] = to

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        try:
            server.login(user, password)
            server.send_message(msg)
        finally:
            server.quit()
