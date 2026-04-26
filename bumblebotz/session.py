"""
Bumble session: uses core BrowserSession and BumbleAdapter.
Exposes the same high-level API as Tinder Session (login, like, dislike, get_geomatch, etc.).
"""
import os
import json
import random
import time
import atexit
from pathlib import Path

from core import BrowserSession, StorageHelper
from core.profile_filters import DEFAULT_REJECT_KEYWORDS_TRANS_GAY, should_reject_profile
from bumblebotz.adapter import BumbleAdapter, BumbleProfile


class Session:
    """Bumble session. Same API as tinderbotz.Session where implemented."""

    HOME_URL = "https://bumble.com/app"

    def __init__(self, headless=False, store_session=True, proxy=None, user_data=False, chrome_version_main=None):
        self.email = None
        self.may_send_email = False
        self.started = None
        self.browser = None
        self.session_data = {"duration": 0, "like": 0, "dislike": 0, "superlike": 0}

        start_session = time.time()

        @atexit.register
        def cleanup():
            seconds = int(time.time() - start_session)
            self.session_data["duration"] = seconds
            lines = [
                "Likes dados: {}".format(self.session_data["like"]),
                "Dislikes dados: {}".format(self.session_data["dislike"]),
                "Superlikes dados: {}".format(self.session_data["superlike"]),
                "Duración (s): {}".format(self.session_data["duration"]),
            ]
            width = max(len(l) for l in lines)
            sep = "=" * (width + 4)
            print("/{}\\".format(sep))
            for l in lines:
                print("| {} |".format(l.ljust(width)))
            print("\\{}/".format(sep))
            print("Started session: {}".format(getattr(self, "started", "N/A")))
            print("Ended session: {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

        user_data_path = f"{Path().absolute()}/chrome_profile_bumble/" if store_session and not user_data else user_data
        browser_session = BrowserSession(
            headless=headless,
            store_session=store_session,
            proxy=proxy,
            user_data=user_data_path,
            version_main=chrome_version_main,
        )
        self.browser = browser_session.browser
        self.started = browser_session.started
        self._adapter = BumbleAdapter(self.browser)

    def is_logged_in(self):
        return self._adapter.is_logged_in()

    def set_custom_location(self, latitude, longitude, accuracy="100%"):
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": int(str(accuracy).split("%")[0]),
        }
        self.browser.execute_cdp_cmd("Page.setGeolocationOverride", params)

    def set_email_notifications(self, boolean):
        self.may_send_email = boolean

    def set_distance_range(self, km):
        self._adapter.set_distance_range(km)

    def set_age_range(self, min_age, max_age):
        self._adapter.set_age_range(min_age, max_age)

    def set_sexuality(self, type):
        self._adapter.set_sexuality(type)

    def set_global(self, boolean):
        self._adapter.set_global(boolean)

    def set_bio(self, bio):
        self._adapter.set_bio(bio)

    def add_photo(self, filepath):
        self._adapter.add_photo(filepath)

    def login_using_google(self, email, password):
        self.email = email
        if not self._adapter.is_logged_in():
            self._adapter.login_using_google(email, password)
            time.sleep(3)
        if not self._adapter.is_logged_in():
            print("Manual interference may be required.")
            input("Press ENTER to continue")

    def login_using_facebook(self, email, password):
        self.email = email
        if not self._adapter.is_logged_in():
            self._adapter.login_using_facebook(email, password)
            time.sleep(3)
        if not self._adapter.is_logged_in():
            print("Manual interference may be required.")
            input("Press ENTER to continue")

    def login_using_sms(self, country, phone_number):
        if not self._adapter.is_logged_in():
            self._adapter.login_using_sms(country, phone_number)
            time.sleep(3)
        if not self._adapter.is_logged_in():
            print("Manual interference may be required.")
            input("Press ENTER to continue")

    def store_local(self, profile):
        if not isinstance(profile, BumbleProfile):
            print("store_local expects BumbleProfile")
            return
        directory = "data/bumble_geomatches"
        if not os.path.exists(directory):
            os.makedirs(directory)
        filepath = os.path.join(directory, "geomatches.json")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except IOError:
            data = {}
        data[profile.get_id()] = {
            "name": profile.get_name(),
            "age": profile.get_age(),
            "bio": profile.get_bio(),
            "image_urls": profile.get_image_urls(),
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f)
        for url in (profile.get_image_urls() or [])[:5]:
            StorageHelper.store_image_as(url=url, directory=os.path.join(directory, "images"))

    def like(
        self,
        amount=1,
        ratio="100%",
        sleep=6.0,
        randomize_sleep=True,
        reject_keywords=None,
        reject_if_male=True,
        reject_profile_emojis=True,
        reject_nonbinary_pronouns=True,
        browse_photos=2,
        browse_photos_delay=0.2,
        **kwargs,
    ):
        """
        Like con delay 4-8 s. Filtros opcionales (misma lógica que Tinder):
        - reject_keywords: None = lista por defecto (trans / gay / LGBTQ+); [] = sin palabras clave.
        - reject_profile_emojis: 🏳️‍⚧️, ⚧️, 🏳️‍🌈, 🌈, ⚢, ⚣, ⚥.
        - reject_nonbinary_pronouns: they/them, ze/zir, xe/xem, fae/faer, pronombres mixtos he+she.
        """
        if not self._adapter.is_logged_in():
            return
        if reject_keywords is None:
            reject_keywords = list(DEFAULT_REJECT_KEYWORDS_TRANS_GAY)
        use_filters = bool(reject_keywords or reject_if_male or reject_profile_emojis)
        ratio_val = float(str(ratio).split("%")[0]) / 100
        amount_liked = 0
        min_sleep = 4.0
        max_sleep = 8.0
        for i in range(amount):
            t0 = time.time()
            self._adapter.handle_popups()
            if i > 0:
                time.sleep(1.2)
            profile = self._adapter.get_current_profile(
                quickload=True,
                browse_photos=browse_photos if use_filters else 0,
                browse_photos_delay=browse_photos_delay,
            )
            name = (profile.get_name() or "").strip() if profile else ""
            age = profile.get_age() if profile else None
            if not name:
                name = "—"
            if use_filters and profile:
                rejected, reason = should_reject_profile(
                    profile, reject_keywords, reject_if_male,
                    reject_profile_emojis, reject_nonbinary_pronouns
                )
                if rejected:
                    print("  Descartado Filtro: {}".format(reason))
                    self._adapter.dislike()
                    self.session_data["dislike"] += 1
                    delay = random.uniform(min_sleep, max_sleep) if randomize_sleep else sleep
                    time.sleep(delay)
                    elapsed = time.time() - t0
                    if age is not None:
                        print('Descartado (filtro) - "{}" {} - {:.1f}s'.format(name, age, elapsed))
                    else:
                        print('Descartado (filtro) - "{}" - {:.1f}s'.format(name, elapsed))
                    continue
            do_like = random.random() <= ratio_val
            if do_like:
                if self._adapter.like():
                    amount_liked += 1
                    self.session_data["like"] += 1
                    delay = random.uniform(min_sleep, max_sleep) if randomize_sleep else sleep
                    time.sleep(delay)
                    elapsed = time.time() - t0
                    if age is not None:
                        print('Like {}/{} - "{}" {} - {:.1f}s'.format(
                            amount_liked, amount, name, age, elapsed
                        ))
                    else:
                        print('Like {}/{} - "{}" - {:.1f}s'.format(
                            amount_liked, amount, name, elapsed
                        ))
                else:
                    self.session_data["dislike"] += 1
                    delay = random.uniform(min_sleep, max_sleep) if randomize_sleep else sleep
                    time.sleep(delay)
                    elapsed = time.time() - t0
                    if age is not None:
                        print('Pass {}/{} - "{}" {} - {:.1f}s'.format(
                            amount_liked, amount, name, age, elapsed
                        ))
                    else:
                        print('Pass {}/{} - "{}" - {:.1f}s'.format(
                            amount_liked, amount, name, elapsed
                        ))
            else:
                self._adapter.dislike()
                self.session_data["dislike"] += 1
                delay = random.uniform(min_sleep, max_sleep) if randomize_sleep else sleep
                time.sleep(delay)
                elapsed = time.time() - t0
                if age is not None:
                    print('Descartado (ratio) - "{}" {} - {:.1f}s'.format(
                        name, age, elapsed
                    ))
                else:
                    print('Descartado (ratio) - "{}" - {:.1f}s'.format(
                        name, elapsed
                    ))

    def dislike(self, amount=1):
        if not self._adapter.is_logged_in():
            return
        for _ in range(amount):
            self._adapter.handle_popups()
            self._adapter.dislike()
            self.session_data["dislike"] += 1

    def superlike(self, amount=1):
        if not self._adapter.is_logged_in():
            return
        for _ in range(amount):
            self._adapter.handle_popups()
            self._adapter.superlike()
            self.session_data["superlike"] += 1
            time.sleep(1)

    def get_geomatch(self, quickload=True, browse_photos=1, browse_photos_delay=0.2):
        if not self._adapter.is_logged_in():
            return None
        self._adapter.handle_popups()
        return self._adapter.get_current_profile(
            quickload=quickload, browse_photos=browse_photos, browse_photos_delay=browse_photos_delay
        )

    def get_chat_ids(self, new=True, messaged=True):
        return self._adapter.get_chat_ids(new, messaged) if self._adapter.is_logged_in() else []

    def get_new_matches(self, amount=100000, quickload=True):
        return self._adapter.get_new_matches(amount, quickload) if self._adapter.is_logged_in() else []

    def get_messaged_matches(self, amount=100000, quickload=True):
        return self._adapter.get_messaged_matches(amount, quickload) if self._adapter.is_logged_in() else []

    def send_message(self, chatid, message):
        if self._adapter.is_logged_in():
            self._adapter.send_message(chatid, message)

    def send_gif(self, chatid, gifname):
        if self._adapter.is_logged_in():
            self._adapter.send_gif(chatid, gifname)

    def send_song(self, chatid, songname):
        if self._adapter.is_logged_in():
            self._adapter.send_song(chatid, songname)

    def send_socials(self, chatid, media):
        if self._adapter.is_logged_in():
            self._adapter.send_socials(chatid, media)

    def unmatch(self, chatid):
        if self._adapter.is_logged_in():
            self._adapter.unmatch(chatid)
