"""
Tinder implementation of PlatformAdapter. Uses Tinder helpers and xpaths.
"""
import time
from typing import List, Any, Optional

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementNotVisibleException,
)

from tinderbotz.helpers.xpaths import content, modal_manager
from tinderbotz.helpers.geomatch import Geomatch
from tinderbotz.helpers.geomatch_helper import GeomatchHelper
from tinderbotz.helpers.match_helper import MatchHelper
from tinderbotz.helpers.login_helper import LoginHelper
from tinderbotz.helpers.preferences_helper import PreferencesHelper
from tinderbotz.helpers.profile_helper import ProfileHelper


class TinderAdapter:
    """PlatformAdapter for Tinder. Delegates to existing helpers."""

    HOME_URL = "https://www.tinder.com/es/app/recs"
    APP_BASE_URL = "https://www.tinder.com/es/app"

    def __init__(self, browser):
        self.browser = browser

    def navigate_to(self, path: str) -> None:
        """
        Navega a una sección de Tinder (recs, explore, explore/events, etc.).
        path: ruta relativa a /app/, sin barra inicial. Ej: "recs", "explore", "explore/events".
        """
        path = (path or "recs").strip().lstrip("/")
        url = f"{self.APP_BASE_URL}/{path}" if path else self.APP_BASE_URL
        self.browser.get(url)
        time.sleep(2)

    def handle_popups(self) -> Optional[str]:
        delay = 0.25
        try:
            base_element = self.browser.find_element(By.XPATH, modal_manager)
        except Exception:
            return None

        for xpath in [
            "//*[contains(text(), 'No, gracias')]",
            "//*[contains(text(), 'No gracias')]",
            "//*[contains(., 'No, gracias')]",
            "//*[contains(., 'No gracias')]",
        ]:
            try:
                el = self.browser.find_element(By.XPATH, xpath)
                if el.is_displayed():
                    el.click()
                    time.sleep(0.3)
                    return "POPUP: No gracias a Super Like"
            except Exception:
                continue

        try:
            xpath = './/main/div/div/div[3]/button[2]'
            WebDriverWait(base_element, delay).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            deny_btn = base_element.find_element(By.XPATH, xpath)
            deny_btn.click()
            return "POPUP: Denied see who liked you"
        except (NoSuchElementException, TimeoutException):
            pass

        try:
            xpath = './/main/div/button[2]'
            base_element.find_element(By.XPATH, xpath).click()
            return "POPUP: Denied upgrade to superlike"
        except NoSuchElementException:
            pass

        try:
            xpath = './/main/div/div[2]/button[2]'
            base_element.find_element(By.XPATH, xpath).click()
            return "POPUP: Denied Tinder to homescreen"
        except NoSuchElementException:
            pass

        try:
            xpath = './/main/div/div[3]/button[2]'
            base_element.find_element(By.XPATH, xpath).click()
            return "POPUP: Denied buying more superlikes"
        except NoSuchElementException:
            pass

        matched = False
        try:
            xpath = '//button[@title="Back to Tinder"]'
            base_element.find_element(By.XPATH, xpath).click()
            matched = True
        except NoSuchElementException:
            pass
        except Exception:
            matched = True
            self.browser.refresh()

        if matched:
            return "POPUP: Dismissed NEW MATCH"

        try:
            xpath = './/main/div/div[3]/button[2]'
            base_element.find_element(By.XPATH, xpath).click()
            return "POPUP: Denied buying more superlikes"
        except ElementNotVisibleException:
            self.browser.refresh()
        except NoSuchElementException:
            pass
        except Exception:
            self.browser.refresh()

        try:
            xpath = './/main/div/div[1]/div[2]/button[2]'
            base_element.find_element(By.XPATH, xpath).click()
            time.sleep(3)
            return self.handle_popups() or "POPUP: Deny confirmation of email"
        except Exception:
            pass

        try:
            xpath = ".//*[contains(text(), 'No Thanks')]"
            base_element.find_element(By.XPATH, xpath).click()
            time.sleep(3)
            return self.handle_popups() or "POPUP: Deny confirmation of email"
        except Exception:
            pass

        return None

    def is_logged_in(self) -> bool:
        if "tinder" not in self.browser.current_url:
            self.browser.get("https://tinder.com/?lang=es")
            time.sleep(1.5)
        if "tinder.com/app/" in self.browser.current_url:
            return True
        print("User is not logged in yet.\n")
        return False

    def login_using_google(self, email: str, password: str) -> Optional[str]:
        LoginHelper(self.browser).login_by_google(email, password)
        return None

    def login_using_facebook(self, email: str, password: str) -> Optional[str]:
        LoginHelper(self.browser).login_by_facebook(email, password)
        return None

    def login_using_sms(self, country: str, phone_number: str) -> Optional[str]:
        LoginHelper(self.browser).login_by_sms(country, phone_number)
        return None

    def like(self) -> bool:
        return GeomatchHelper(self.browser).like()

    def dislike(self) -> None:
        GeomatchHelper(self.browser).dislike()

    def superlike(self) -> None:
        GeomatchHelper(self.browser).superlike()

    def get_current_profile(
        self,
        quickload: bool = True,
        browse_photos: int = 1,
        browse_photos_delay: float = 0.10,
    ) -> Optional[Geomatch]:
        helper = GeomatchHelper(self.browser)
        name = None
        for _ in range(2):
            name = helper.get_name()
            if name:
                break
            time.sleep(0.2)
        age = helper.get_age()
        # Bio primero: hace scroll del panel; así las filas (género, trabajo) suelen quedar en DOM visible
        bio, passions, lifestyle, basics, anthem, looking_for = helper.get_bio_and_passions()
        rowdata = helper.get_row_data()
        image_urls = helper.get_image_urls(quickload=True)
        if name and browse_photos > 0:
            helper.browse_photos(num_photos=browse_photos, delay_between=browse_photos_delay)
        instagram = helper.get_insta(bio)
        work = rowdata.get('work')
        study = rowdata.get('study')
        home = rowdata.get('home')
        distance = rowdata.get('distance')
        gender = rowdata.get('gender')
        genders = rowdata.get('genders', [gender] if gender else [])

        return Geomatch(
            name=name, age=age, work=work, gender=gender, study=study, home=home,
            distance=distance, bio=bio, passions=passions, lifestyle=lifestyle,
            basics=basics, anthem=anthem, looking_for=looking_for, image_urls=image_urls,
            instagram=instagram, genders=genders,
        )

    def close_profile(self) -> None:
        GeomatchHelper(self.browser).close_profile()

    def open_profile_and_browse_photos(self, num_photos: int = 1, delay_between: float = 0.10) -> None:
        """Abre el perfil de la carta actual y pasa N fotos (comportamiento humano)."""
        helper = GeomatchHelper(self.browser)
        helper.open_profile()
        time.sleep(0.2)
        helper.browse_photos(num_photos=num_photos, delay_between=delay_between)

    def set_distance_range(self, km: int) -> None:
        PreferencesHelper(self.browser).set_distance_range(km)

    def set_age_range(self, min_age: int, max_age: int) -> None:
        PreferencesHelper(self.browser).set_age_range(min_age, max_age)

    def set_sexuality(self, type: Any) -> None:
        PreferencesHelper(self.browser).set_sexualitiy(type)

    def set_global(self, boolean: bool) -> None:
        PreferencesHelper(self.browser).set_global(boolean)

    def set_bio(self, bio: str) -> None:
        ProfileHelper(self.browser).set_bio(bio)

    def add_photo(self, filepath: str) -> None:
        ProfileHelper(self.browser).add_photo(filepath)

    def get_chat_ids(self, new: bool = True, messaged: bool = True) -> List[str]:
        return MatchHelper(self.browser).get_chat_ids(new, messaged)

    def get_new_matches(self, amount: int = 100000, quickload: bool = True) -> List[Any]:
        return MatchHelper(self.browser).get_new_matches(amount, quickload)

    def get_messaged_matches(self, amount: int = 100000, quickload: bool = True) -> List[Any]:
        return MatchHelper(self.browser).get_messaged_matches(amount, quickload)

    def send_message(self, chatid: str, message: str) -> None:
        MatchHelper(self.browser).send_message(chatid, message)

    def send_gif(self, chatid: str, gifname: str) -> None:
        MatchHelper(self.browser).send_gif(chatid, gifname)

    def send_song(self, chatid: str, songname: str) -> None:
        MatchHelper(self.browser).send_song(chatid, songname)

    def send_socials(self, chatid: str, media: Any) -> None:
        MatchHelper(self.browser).send_socials(chatid, media)

    def unmatch(self, chatid: str) -> None:
        MatchHelper(self.browser).unmatch(chatid)
