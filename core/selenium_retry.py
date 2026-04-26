"""
Reintentos breves ante fallos transitorios de Selenium (stale element, etc.).
"""
import time
from typing import Callable, TypeVar

from selenium.common.exceptions import StaleElementReferenceException, WebDriverException

T = TypeVar("T")


def run_webdriver_action(fn: Callable[[], T], retries: int = 2, delay: float = 0.35) -> T:
    """
    Ejecuta fn(); ante StaleElementReferenceException o WebDriverException recuperables,
    reintenta hasta `retries` veces con pausa `delay`.
    No reintenta sesión inválida o errores de creación de sesión.
    """
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return fn()
        except StaleElementReferenceException as e:
            last_exc = e
        except WebDriverException as e:
            name = type(e).__name__
            if "InvalidSessionId" in name or "SessionNotCreated" in name:
                raise
            last_exc = e
        if attempt < retries:
            time.sleep(delay)
            continue
        break
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("run_webdriver_action: no result")
