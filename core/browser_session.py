"""
Shared browser lifecycle: Chrome (undetected_chromedriver), proxy, user-data-dir, atexit cleanup.
No knowledge of Tinder or Bumble.
"""
import os
import time
import atexit
from pathlib import Path
from typing import Callable, Optional

import undetected_chromedriver as uc
from selenium.common.exceptions import SessionNotCreatedException

from core.addproxy import get_proxy_extension
from core.chrome_version import (
    detect_installed_chrome_major,
    parse_browser_major_from_session_error,
)


def _parse_proxy(proxy: str) -> tuple:
    """
    Valida formato de proxy.
    Devuelve (user, password, host, port) si hay credenciales, o (None, None, host, port) si es host:puerto.
    """
    s = (proxy or "").strip()
    if not s:
        raise ValueError("proxy vacío")
    if "@" in s:
        left, right = s.split("@", 1)
        if ":" not in left or ":" not in right:
            raise ValueError("con credenciales usar usuario:contraseña@host:puerto")
        user, pwd = left.split(":", 1)
        host, port = right.rsplit(":", 1)
        if not user.strip() or not host.strip() or not port.strip():
            raise ValueError("usuario:contraseña@host:puerto incompleto")
        return (user.strip(), pwd, host.strip(), port.strip())
    if ":" not in s:
        raise ValueError("sin credenciales usar host:puerto")
    host, port = s.rsplit(":", 1)
    if not host.strip() or not port.strip():
        raise ValueError("host:puerto incompleto")
    return (None, None, host.strip(), port.strip())


class BrowserSession:
    """Creates and owns the Chrome WebDriver. Caller can pass banner_callback for startup message."""

    def __init__(
        self,
        headless: bool = False,
        store_session: bool = True,
        proxy: Optional[str] = None,
        user_data: Optional[str] = None,
        lang: str = "es-ES",
        version_main: Optional[int] = None,
        banner_callback: Optional[Callable[[], None]] = None,
    ):
        self.browser = None
        self.started = None
        start_session = time.time()

        def cleanup():
            if self.browser is not None:
                try:
                    self.browser.quit()
                except Exception:
                    pass
                self.browser = None

        atexit.register(cleanup)

        options = uc.ChromeOptions()

        if store_session:
            if not user_data:
                user_data = str(Path().absolute() / "chrome_profile")
            if not os.path.isdir(user_data):
                os.mkdir(user_data)
            Path(os.path.join(user_data, "First Run")).touch()
            options.add_argument("--user-data-dir={}".format(user_data))

        options.add_argument("--no-first-run --no-service-autorun --password-store=basic")
        options.add_argument("--lang={}".format(lang))

        if headless:
            options.headless = True

        if proxy:
            try:
                user, pwd, host, port = _parse_proxy(proxy)
            except ValueError as e:
                raise ValueError(
                    "Proxy inválido ({}). Ejemplos: host:8080 o usuario:clave@host:8080".format(e)
                ) from e
            if user is not None:
                extension = get_proxy_extension(
                    PROXY_HOST=host, PROXY_PORT=port, PROXY_USER=user, PROXY_PASS=pwd
                )
                options.add_extension(extension)
            else:
                options.add_argument("--proxy-server=http://{}:{}".format(host, port))

        print("Getting ChromeDriver ...")
        # Alinear con Chrome instalado (registro en Windows); sin esto, uc puede bajar el driver
        # del canal Stable remoto más nuevo que tu navegador.
        vm = version_main
        if vm is None:
            vm = detect_installed_chrome_major()
            if vm is not None:
                print("Chrome instalado (versión mayor): {}".format(vm))

        try:
            if vm is not None:
                self.browser = uc.Chrome(options=options, version_main=vm)
            else:
                self.browser = uc.Chrome(options=options)
        except SessionNotCreatedException as e:
            msg = str(e)
            parsed = parse_browser_major_from_session_error(msg)
            if parsed is not None and parsed != vm:
                print(
                    "ChromeDriver no coincidía con el navegador; reintentando con versión mayor {}.".format(
                        parsed
                    )
                )
                try:
                    self.browser = uc.Chrome(options=options, version_main=parsed)
                except SessionNotCreatedException as e2:
                    hint = (
                        " Tras alinear la versión, el driver sigue fallando. "
                        "Prueba a borrar la caché: %LOCALAPPDATA%\\undetected_chromedriver (Windows)."
                    )
                    raise SessionNotCreatedException(str(e2) + hint) from e2
            else:
                raise
        self.started = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        if banner_callback:
            banner_callback()
        time.sleep(1)
        print("Started session: {}\n\n".format(self.started))
