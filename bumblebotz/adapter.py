"""
Bumble implementation of PlatformAdapter.
Uses Bumble-specific URLs and selectors (see selectors.py).
Implementations are phased: login + like/dislike + popups first; profile and messages as stubs.
"""
import re
import time
from typing import List, Any, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bumblebotz.selectors import (
    BASE_URL,
    LOGIN_URL,
    APP_DISCOVER_URL,
    MESSAGES_URL,
)
from core.selenium_retry import run_webdriver_action


class BumbleProfile:
    """Minimal profile for Bumble (DatingProfile-compatible)."""
    def __init__(self, name=None, age=None, bio=None, image_urls=None, profile_id=None):
        self.name = name
        self.age = age
        self.bio = bio
        self.image_urls = image_urls or []
        self.id = profile_id or (f"{name or 'unknown'}{age or 0}")
        self.genders = []
        self.passions = None
        self.lifestyle = None
        self.basics = None
        self.looking_for = None

    def get_name(self): return self.name
    def get_age(self): return self.age
    def get_bio(self): return self.bio
    def get_image_urls(self): return self.image_urls
    def get_id(self): return self.id
    def get_genders(self): return self.genders
    def get_passions(self): return self.passions
    def get_lifestyle(self): return self.lifestyle
    def get_basics(self): return self.basics
    def get_looking_for(self): return self.looking_for


class BumbleAdapter:
    """PlatformAdapter for Bumble. Uses placeholder selectors until Bumble DOM is inspected."""

    HOME_URL = APP_DISCOVER_URL

    # Keywords de género para detección exacta (tags/badges cortos)
    _MALE_GENDER_EXACT = frozenset({
        "man", "men", "hombre", "male", "chico", "homme", "homem",
        "masculino", "boy", "uomo", "männlich", "macho",
    })
    _FEMALE_GENDER_EXACT = frozenset({
        "woman", "women", "mujer", "female", "chica", "femme", "mulher",
        "donna", "femenino", "weiblich", "girl", "chicas",
    })
    _FEMALE_GENDER_SUBSTR = (
        "woman", "women", "mujer", "female", "chica", "femme",
        "mulher", "donna", "femenino", "girl",
    )

    def __init__(self, browser):
        self.browser = browser

    def handle_popups(self) -> Optional[str]:
        # Placeholder: try common close/dismiss patterns
        for xpath in [
            "//button[contains(@aria-label, 'Close')]",
            "//*[contains(text(), 'Not now')]",
            "//*[contains(text(), 'No thanks')]",
            "//*[contains(text(), 'Maybe later')]",
        ]:
            try:
                el = self.browser.find_element(By.XPATH, xpath)
                if el.is_displayed():
                    el.click()
                    time.sleep(0.3)
                    return "POPUP: Dismissed"
            except Exception:
                continue
        return None

    @staticmethod
    def _url_looks_logged_in(url: Optional[str]) -> bool:
        """True si la URL indica sesión en la web de Bumble (incl. rutas con locale)."""
        u = (url or "").lower()
        path = u.split("?", 1)[0]
        if "bumble.com" not in u:
            return False
        if "get-started" in path and "/app" not in path:
            return False
        if ("/sign-in" in path or "/signin" in path) and "/app" not in path:
            return False
        if "/app" in path and "get-started" not in path:
            return True
        if any(p in path for p in ("/discover", "/matches", "/encounters")):
            return True
        return False

    def is_logged_in(self) -> bool:
        if self._url_looks_logged_in(self.browser.current_url):
            return True

        # Ir al área de la app (la home suele tardar o no redirigir con poco tiempo)
        self.browser.get(APP_DISCOVER_URL)
        time.sleep(0.5)
        deadline = time.time() + 25.0
        while time.time() < deadline:
            cur = self.browser.current_url or ""
            if self._url_looks_logged_in(cur):
                return True
            cu = (cur or "").lower().split("?", 1)[0]
            if "get-started" in cu and "/app" not in cu:
                return False
            time.sleep(0.35)
        return self._url_looks_logged_in(self.browser.current_url)

    def login_using_google(self, email: str, password: str) -> Optional[str]:
        self.browser.get(LOGIN_URL)
        time.sleep(2)
        self.handle_popups()
        # Bumble web may use Facebook/Apple/phone more than Google – placeholder
        try:
            # Try "Continue with Google" if present
            btn = self.browser.find_element(By.XPATH, "//*[contains(text(), 'Google') or contains(@aria-label, 'Google')]")
            btn.click()
            time.sleep(2)
            # Switch to Google popup and fill email/password (same as Tinder flow)
            for handle in self.browser.window_handles:
                self.browser.switch_to.window(handle)
                if "accounts.google" in self.browser.current_url:
                    break
            email_el = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
            )
            email_el.send_keys(email)
            email_el.send_keys(Keys.ENTER)
            time.sleep(2)
            pwd_el = self.browser.find_element(By.XPATH, "//input[@type='password']")
            pwd_el.send_keys(password)
            pwd_el.send_keys(Keys.ENTER)
            time.sleep(3)
            self.browser.switch_to.window(self.browser.window_handles[0])
        except Exception as e:
            print("Bumble Google login placeholder failed: {}".format(str(e)[:80]))
        return None

    def login_using_facebook(self, email: str, password: str) -> Optional[str]:
        self.browser.get(LOGIN_URL)
        time.sleep(2)
        self.handle_popups()
        try:
            btn = self.browser.find_element(By.XPATH, "//*[contains(text(), 'Facebook') or contains(@aria-label, 'Facebook')]")
            btn.click()
            time.sleep(2)
            for handle in self.browser.window_handles:
                self.browser.switch_to.window(handle)
                if "facebook" in self.browser.current_url:
                    break
            email_el = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
            )
            email_el.send_keys(email)
            self.browser.find_element(By.XPATH, "//input[@type='password']").send_keys(password)
            self.browser.find_element(By.NAME, "login").click()
            time.sleep(3)
            self.browser.switch_to.window(self.browser.window_handles[0])
        except Exception as e:
            print("Bumble Facebook login placeholder failed: {}".format(str(e)[:80]))
        return None

    def login_using_sms(self, country: str, phone_number: str) -> Optional[str]:
        self.browser.get(LOGIN_URL)
        time.sleep(2)
        self.handle_popups()
        try:
            # Buscar opción de login por teléfono
            for xpath in (
                "//*[contains(@aria-label, 'phone') or contains(@aria-label, 'teléfono') or contains(@aria-label, 'Phone')]",
                "//*[contains(text(), 'phone') or contains(text(), 'teléfono') or contains(text(), 'Phone') or contains(text(), 'número')]",
                "//input[@type='tel' or @inputmode='tel']",
            ):
                try:
                    el = self.browser.find_element(By.XPATH, xpath)
                    if el.is_displayed():
                        el.click()
                        time.sleep(1)
                        break
                except Exception:
                    continue
            # Rellenar número
            phone_input = self.browser.find_element(By.XPATH, "//input[@type='tel' or @inputmode='tel' or contains(@name,'phone') or contains(@placeholder,'phone')]")
            phone_input.clear()
            phone_input.send_keys(phone_number)
            time.sleep(0.5)
            # Enviar / continuar
            for btn_xpath in (
                "//button[contains(., 'Continue') or contains(., 'Continuar') or contains(., 'Next') or contains(., 'Siguiente')]",
                "//*[@type='submit']",
            ):
                try:
                    btn = self.browser.find_element(By.XPATH, btn_xpath)
                    if btn.is_displayed():
                        btn.click()
                        break
                except Exception:
                    continue
            time.sleep(2)
            # Código SMS (pedir por consola)
            code = input("Código SMS recibido: ").strip()
            code_el = self.browser.find_element(By.XPATH, "//input[@type='text' or @type='tel' or @inputmode='numeric'][contains(@placeholder,'code') or contains(@placeholder,'código') or contains(@name,'code') or contains(@name,'otp')]")
            code_el.clear()
            code_el.send_keys(code)
            time.sleep(0.5)
            for btn_xpath in (
                "//button[contains(., 'Continue') or contains(., 'Continuar') or contains(., 'Verify') or contains(., 'Verificar')]",
                "//*[@type='submit']",
            ):
                try:
                    btn = self.browser.find_element(By.XPATH, btn_xpath)
                    if btn.is_displayed():
                        btn.click()
                        break
                except Exception:
                    continue
            time.sleep(3)
        except Exception as e:
            print("Bumble SMS login failed: {}".format(str(e)[:120]))
        return None

    def like(self) -> bool:
        try:
            def _keys():
                ActionChains(self.browser).send_keys(Keys.ARROW_RIGHT).perform()

            run_webdriver_action(_keys, retries=2, delay=0.35)
            return True
        except Exception:
            pass
        try:
            def _click():
                btn = self.browser.find_element(
                    By.XPATH,
                    "//button[contains(@aria-label, 'Like') or contains(@class, 'like') or contains(., 'Yes')]",
                )
                btn.click()

            run_webdriver_action(_click, retries=2, delay=0.35)
            return True
        except Exception:
            pass
        return False

    def dislike(self) -> None:
        try:
            def _keys():
                ActionChains(self.browser).send_keys(Keys.ARROW_LEFT).perform()

            run_webdriver_action(_keys, retries=2, delay=0.35)
        except Exception:
            try:
                def _click():
                    btn = self.browser.find_element(
                        By.XPATH,
                        "//button[contains(@aria-label, 'Pass') or contains(@class, 'pass') or contains(., 'No')]",
                    )
                    btn.click()

                run_webdriver_action(_click, retries=2, delay=0.35)
            except Exception:
                pass

    def superlike(self) -> None:
        # Bumble may have "SuperSwipe" equivalent – stub
        self.like()

    # Textos de navegación que no son el nombre del perfil (evitar "Matches", "Conversaciones (Recientes)", etc.)
    _NAV_SKIP = frozenset({
        "matches", "bumble", "date", "bff", "chat", "discover", "likes", "notes",
        "conversations", "conversaciones", "recientes", "profile", "settings", "search", "busco",
    })
    _NAV_SKIP_SUBSTR = ("conversaciones", "recientes", "matches", "bumble", "discover", "chat", "notes", "likes")

    def _get_profile_container(self):
        """Contenedor de la tarjeta actual (con like/pass) para no leer texto del sidebar."""
        for xpath in (
            "//*[contains(@class,'encounter') or contains(@class,'card')][.//*[contains(@aria-label,'Like') or contains(@aria-label,'Pass') or contains(@class,'like') or contains(@class,'pass')]]",
            "//main//*[.//*[contains(@aria-label,'Like') or contains(@aria-label,'Pass')]]",
            "//*[contains(@class,'encounter')]",
            "//*[contains(@class,'card') and contains(@class,'profile')]",
        ):
            try:
                for el in self.browser.find_elements(By.XPATH, xpath):
                    if el.is_displayed():
                        return el
            except Exception:
                continue
        return None

    def _detect_gender(self, container) -> Optional[str]:
        """
        Detecta el género del perfil actual. Tres capas (misma filosofía que Tinder):

        1. Texto exacto de elementos cortos: los tags de género en Bumble son
           píldoras/badges de una palabra ("Woman", "Man", "Mujer"...).
        2. Selectores semánticos: class/aria-label/data-qa con 'gender'.
        3. Scan de bio solo para femenino: evita el falso positivo de una mujer
           que escriba "busco un hombre..." en su bio.
        """
        scope = container if container else self.browser

        _all_gender_kw = self._FEMALE_GENDER_EXACT | self._MALE_GENDER_EXACT

        # Capa 1: badges / tags cortos. Soporta géneros compuestos ("Mujer trans", "Trans Woman").
        # Se devuelve el texto COMPLETO para que los filtros downstream detecten "trans" etc.
        try:
            for el in scope.find_elements(By.XPATH, ".//*[self::span or self::div or self::p]"):
                if not el.is_displayed():
                    continue
                text = (el.text or "").strip()
                if not text or len(text) > 40:
                    continue
                words = set(text.lower().split())
                if words & _all_gender_kw:
                    return text
        except Exception:
            pass

        # Capa 2: selectores semánticos que Bumble suele usar
        for xpath in (
            "//*[contains(@class,'gender')]",
            "//*[contains(@aria-label,'gender') or contains(@aria-label,'Gender')]",
            "//*[contains(@data-qa,'gender')]",
            "//*[contains(@class,'profile-info')]//span",
            "//*[contains(@class,'about')]//span",
        ):
            try:
                for el in self.browser.find_elements(By.XPATH, xpath):
                    if not el.is_displayed():
                        continue
                    text = (el.text or "").strip()
                    if not text or len(text) > 40:
                        continue
                    words = set(text.lower().split())
                    if words & _all_gender_kw:
                        return text
            except Exception:
                continue

        # Capa 3: bio solo femenino (no infiere masculino del texto libre)
        try:
            text = (scope.get_attribute("innerText") or scope.text or "").lower()
            for word in self._FEMALE_GENDER_SUBSTR:
                if word in text:
                    return word.capitalize()
        except Exception:
            pass

        return None

    def get_current_profile(
        self,
        quickload: bool = True,
        browse_photos: int = 1,
        browse_photos_delay: float = 0.2,
    ) -> Optional[BumbleProfile]:
        name = None
        age = None
        container = self._get_profile_container()
        scope = container if container else self.browser
        xpath_list = (".//h1", ".//h2", ".//*[contains(@class,'name') or contains(@class,'title')]") if container else (
            "//main//h1", "//main//*[contains(@class,'profile')]//h1", "//*[contains(@class,'encounter')]//h1",
            "//*[contains(@class,'card')]//h1", "//main//*[@class and contains(translate(@class,'N','n'),'name')]", "//h1",
        )
        fallback_xpaths = (
            "//main//h1", "//main//*[contains(@class,'profile')]//h1", "//*[contains(@class,'encounter')]//h1",
            "//*[contains(@class,'card')]//h1", "//main//*[@class and contains(translate(@class,'N','n'),'name')]", "//h1",
        )
        for xpath in xpath_list:
            try:
                els = scope.find_elements(By.XPATH, xpath)
                for el in els:
                    if not el.is_displayed():
                        continue
                    raw = (el.text or "").strip().replace("\n", " ")
                    if not raw or len(raw) > 50:
                        continue
                    raw_lower = raw.lower()
                    if raw_lower in self._NAV_SKIP:
                        continue
                    if any(s in raw_lower for s in self._NAV_SKIP_SUBSTR):
                        continue
                    # "Name, 25" o "Name 25" -> nombre y edad
                    match = re.match(r"^(.+?)\s*[,]\s*(\d{2,3})\s*$", raw)
                    if match:
                        name = match.group(1).strip()
                        age = int(match.group(2))
                        break
                    match = re.match(r"^(.+?)\s+(\d{2,3})\s*$", raw)
                    if match:
                        name = match.group(1).strip()
                        age = int(match.group(2))
                        break
                    if raw and not raw.isdigit():
                        name = raw
                        try:
                            parent = el.find_element(By.XPATH, "..")
                            sib = parent.find_elements(By.XPATH, ".//*[string-length(normalize-space(text()))>0]")
                            for s in sib:
                                t = (s.text or "").strip()
                                if t.isdigit() and 18 <= int(t) <= 99:
                                    age = int(t)
                                    break
                        except Exception:
                            pass
                        break
                    if name:
                        break
                if name:
                    break
            except Exception:
                continue
        if not name and container:
            for xpath in fallback_xpaths:
                try:
                    els = self.browser.find_elements(By.XPATH, xpath)
                    for el in els:
                        if not el.is_displayed():
                            continue
                        raw = (el.text or "").strip().replace("\n", " ")
                        if not raw or len(raw) > 50:
                            continue
                        raw_lower = raw.lower()
                        if raw_lower in self._NAV_SKIP or any(s in raw_lower for s in self._NAV_SKIP_SUBSTR):
                            continue
                        match = re.match(r"^(.+?)\s*[,]\s*(\d{2,3})\s*$", raw)
                        if match:
                            name = match.group(1).strip()
                            age = int(match.group(2))
                            break
                        match = re.match(r"^(.+?)\s+(\d{2,3})\s*$", raw)
                        if match:
                            name = match.group(1).strip()
                            age = int(match.group(2))
                            break
                        if raw and not raw.isdigit():
                            name = raw
                            break
                    if name:
                        break
                except Exception:
                    continue
        if name and (name.lower() in self._NAV_SKIP or any(s in name.lower() for s in self._NAV_SKIP_SUBSTR)):
            name = None
        if not age and name:
            try:
                age_els = self.browser.find_elements(By.XPATH, "//main//*[contains(@class,'age') or contains(., ' years')]")
                for ae in age_els:
                    if not ae.is_displayed():
                        continue
                    t = (ae.text or "").strip()
                    if t.isdigit() and 18 <= int(t) <= 99:
                        age = int(t)
                        break
                    m = re.search(r"(\d{2})\s*years?", t, re.I)
                    if m and 18 <= int(m.group(1)) <= 99:
                        age = int(m.group(1))
                        break
            except Exception:
                pass
        urls = []
        try:
            imgs = self.browser.find_elements(By.XPATH, "//main//img[contains(@src, 'bumble') or contains(@src, 'image')] | //*[contains(@class,'encounter')]//img | //*[contains(@class,'card')]//img")
            for img in imgs[:5]:
                src = img.get_attribute("src")
                if src and "http" in src:
                    urls.append(src)
        except Exception:
            pass
        # Scroll the card to trigger lazy-render of bio sections before reading text
        if container:
            try:
                self.browser.execute_script(
                    "var e=arguments[0]; e.scrollTop=Math.min(e.scrollTop+600, e.scrollHeight);",
                    container,
                )
                time.sleep(0.25)
            except Exception:
                pass
        bio = None
        if container:
            try:
                raw = (container.get_attribute("innerText") or container.text or "").strip()
                if raw and len(raw) > 3:
                    bio = raw
            except Exception:
                pass
        # Fallback: read from //main if container bio is absent or suspiciously short
        if not bio or len(bio) < 40:
            try:
                main_el = self.browser.find_element(By.TAG_NAME, "main")
                raw = (main_el.get_attribute("innerText") or main_el.text or "").strip()
                if raw and len(raw) > len(bio or ""):
                    bio = raw
            except Exception:
                pass
        profile = BumbleProfile(name=name, age=age, bio=bio, image_urls=urls or None)
        detected_gender = self._detect_gender(container)
        if detected_gender:
            profile.genders = [detected_gender]
        return profile

    def close_profile(self) -> None:
        try:
            close_btn = self.browser.find_element(By.XPATH, "//button[@aria-label='Close'] | //*[contains(@class, 'close')]")
            close_btn.click()
        except Exception:
            pass

    def set_distance_range(self, km: int) -> None:
        raise NotImplementedError("Bumble set_distance_range not yet implemented")

    def set_age_range(self, min_age: int, max_age: int) -> None:
        raise NotImplementedError("Bumble set_age_range not yet implemented")

    def set_sexuality(self, type: Any) -> None:
        raise NotImplementedError("Bumble set_sexuality not yet implemented")

    def set_global(self, boolean: bool) -> None:
        raise NotImplementedError("Bumble set_global not yet implemented")

    def set_bio(self, bio: str) -> None:
        raise NotImplementedError("Bumble set_bio not yet implemented")

    def add_photo(self, filepath: str) -> None:
        raise NotImplementedError("Bumble add_photo not yet implemented")

    def get_chat_ids(self, new: bool = True, messaged: bool = True) -> List[str]:
        raise NotImplementedError("Bumble get_chat_ids not yet implemented")

    def get_new_matches(self, amount: int = 100000, quickload: bool = True) -> List[Any]:
        raise NotImplementedError("Bumble get_new_matches not yet implemented")

    def get_messaged_matches(self, amount: int = 100000, quickload: bool = True) -> List[Any]:
        raise NotImplementedError("Bumble get_messaged_matches not yet implemented")

    def send_message(self, chatid: str, message: str) -> None:
        raise NotImplementedError("Bumble send_message not yet implemented")

    def send_gif(self, chatid: str, gifname: str) -> None:
        raise NotImplementedError("Bumble send_gif not yet implemented")

    def send_song(self, chatid: str, songname: str) -> None:
        raise NotImplementedError("Bumble send_song not yet implemented")

    def send_socials(self, chatid: str, media: Any) -> None:
        raise NotImplementedError("Bumble send_socials not yet implemented")

    def unmatch(self, chatid: str) -> None:
        raise NotImplementedError("Bumble unmatch not yet implemented")
