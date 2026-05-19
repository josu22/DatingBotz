# Core: browser session and storage
from core import BrowserSession, StorageHelper
from core.profile_filters import DEFAULT_REJECT_KEYWORDS_TRANS_GAY, should_reject_profile
from core.photo_preference_model import PhotoPreferenceModel

import os
import time
import random
import atexit
from pathlib import Path

# Tinderbotz
from tinderbotz.helpers.geomatch import Geomatch
from tinderbotz.helpers.match import Match
from tinderbotz.helpers.email_helper import EmailHelper
from tinderbotz.helpers.constants_helper import Printouts
from tinderbotz.adapter import TinderAdapter


class Session:
    HOME_URL = "https://www.tinder.com/es/app/recs"

    def __init__(self, headless=False, store_session=True, proxy=None, user_data=False, chrome_version_main=None):
        self.email = None
        self.may_send_email = False
        self.started = None
        self.browser = None
        self.session_data = {
            "duration": 0,
            "like": 0,
            "dislike": 0,
            "superlike": 0
        }

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
            try:
                box = self._get_msg_box(lines=lines, title="Tinderbotz")
                print(box)
            finally:
                print("Started session: {}".format(getattr(self, 'started', 'N/A')))
                y = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print("Ended session: {}".format(y))
            # BrowserSession's atexit handles browser.quit()

        user_data_path = f"{Path().absolute()}/chrome_profile_tinder/" if store_session and not user_data else user_data
        browser_session = BrowserSession(
            headless=headless,
            store_session=store_session,
            proxy=proxy,
            user_data=user_data_path,
            version_main=chrome_version_main,
            banner_callback=lambda: print(Printouts.BANNER.value),
        )
        self.browser = browser_session.browser
        self.started = browser_session.started
        self._adapter = TinderAdapter(self.browser)

    # Setting a custom location
    def set_custom_location(self, latitude, longitude, accuracy="100%"):

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": int(accuracy.split('%')[0])
        }

        self.browser.execute_cdp_cmd("Page.setGeolocationOverride", params)

    # This will send notification when you get a match to your email used to logged in.
    def set_email_notifications(self, boolean):
        self.may_send_email = boolean

    # NOTE: Need to be logged in for this
    def set_distance_range(self, km):
        self._adapter.set_distance_range(km)

    def set_age_range(self, min, max):
        self._adapter.set_age_range(min, max)

    def set_sexuality(self, type):
        self._adapter.set_sexuality(type)

    def set_global(self, boolean):
        self._adapter.set_global(boolean)

    def set_bio(self, bio):
        self._adapter.set_bio(bio)

    def add_photo(self, filepath):
        self._adapter.add_photo(filepath)

    def is_logged_in(self):
        return self._is_logged_in()

    def navigate_to(self, path):
        """
        Navega a otra sección de Tinder para dar likes ahí.
        path: "recs" (recomendaciones), "explore", "explore/events", "explore/***", etc.
        """
        if self._is_logged_in():
            self._adapter.navigate_to(path)

    # Actions of the session
    def login_using_google(self, email, password):
        self.email = email
        if not self._is_logged_in():
            self._adapter.login_using_google(email, password)
            time.sleep(3)
        if not self._is_logged_in():
            print('Manual interference is required.')
            input('press ENTER to continue')

    def login_using_facebook(self, email, password):
        self.email = email
        if not self._is_logged_in():
            self._adapter.login_using_facebook(email, password)
            time.sleep(3)
        if not self._is_logged_in():
            print('Manual interference is required.')
            input('press ENTER to continue')

    def login_using_sms(self, country, phone_number):
        if not self._is_logged_in():
            self._adapter.login_using_sms(country, phone_number)
            time.sleep(3)
        if not self._is_logged_in():
            print('Manual interference is required.')
            input('press ENTER to continue')

    def store_local(self, match):
        if isinstance(match, Match):
            filename = 'matches'
        elif isinstance(match, Geomatch):
            filename = 'geomatches'
        else:
            print("type of match is unknown, storing local impossible")
            print("Crashing in 3.2.1... :)")
            assert False

        # store its images
        for url in match.image_urls:
            hashed_image = StorageHelper.store_image_as(url=url, directory='data/{}/images'.format(filename))
            match.images_by_hashes.append(hashed_image)

        # store its userdata
        StorageHelper.store_match(match=match, directory='data/{}'.format(filename), filename=filename)

    def _save_liked_photos(self, geomatch, base_dir='data/liked', saved_name=None, saved_age=None):
        """Guarda la primera foto en data/liked como Nombre-Edad.jpg. Usar saved_name y saved_age capturados al dar like (misma chica)."""
        if not geomatch:
            return
        image_urls = getattr(geomatch, 'image_urls', None) or []
        if not image_urls:
            return
        image_urls = image_urls[:1]
        directory = os.path.normpath(base_dir)
        if not os.path.isabs(directory):
            directory = os.path.join(os.getcwd(), directory)
        os.makedirs(directory, exist_ok=True)
        name = (saved_name if saved_name is not None else (geomatch.get_name() or "")).strip() or "perfil"
        age = saved_age if saved_age is not None else geomatch.get_age()
        filename_base = "{}-{}".format(name, age if age is not None else "0")
        for url in image_urls:
            try:
                StorageHelper.store_image_as(
                    url=url, directory=directory, custom_filename=filename_base
                )
            except Exception:
                pass

    def like(self, amount=1, ratio='100%', sleep=2, randomize_sleep=True,
             reject_keywords=None, reject_if_male=True, reject_profile_emojis=True,
             reject_nonbinary_pronouns=True,
             photo_model_threshold=None,
             save_liked_photos=False, liked_photos_dir='data/liked',
             browse_photos=3, browse_photos_delay=0.10, browse_before_like=1):
        """
        Dar like a perfiles. Opcionalmente filtrar por palabras clave y género.

        - reject_keywords: None = lista por defecto (trans / gay / LGBTQ+ en texto). [] = sin filtro por palabras.
        - reject_profile_emojis: 🏳️‍⚧️, ⚧️, 🏳️‍🌈, 🌈, ⚢, ⚣, ⚥ en nombre/bio/…
        - reject_nonbinary_pronouns: they/them, ze/zir, xe/xem, fae/faer, pronombres mixtos he+she.
        - reject_if_male: género masculino declarado en la app.
        - save_liked_photos / liked_photos_dir: guardar fotos de los likes.
        - browse_photos: al abrir perfil, pasar N fotos (comportamiento humano). 0 = no pasar.
        - browse_photos_delay: segundos entre cada foto al pasarlas (default 0.10).
        - browse_before_like: si > 0, abre perfil, pasa N fotos y cierra antes de like/dislike (default 1, siempre activo).
        - sleep: pausa tras cada like (default 2 s); con randomize_sleep se aplica un factor aleatorio.
        - photo_model_threshold: float 0-1 o None. Si se especifica (ej. 0.4), usa el modelo
          entrenado con collect_training_data/train_preference_model como filtro adicional.
          Un perfil cuya foto principal obtenga un score inferior al umbral será descartado.
        """
        initial_sleep = sleep
        ratio = float(ratio.split('%')[0]) / 100
        if reject_keywords is None:
            reject_keywords = list(DEFAULT_REJECT_KEYWORDS_TRANS_GAY)
        use_filters = bool(reject_keywords or reject_if_male or reject_profile_emojis or reject_nonbinary_pronouns)

        # Cargar modelo de preferencias si se solicita
        _photo_model = None
        if photo_model_threshold is not None:
            _photo_model = PhotoPreferenceModel()
            if _photo_model.load():
                use_filters = True
                print("  Modelo de preferencias cargado (umbral={:.2f})".format(photo_model_threshold))
            else:
                print("  AVISO: no se encontró modelo entrenado. Ejecuta train_preference_model() primero.")
                _photo_model = None

        if self._is_logged_in():
            amount_liked = 0
            self._handle_potential_popups()
            max_iterations = amount * 5 + 30
            iteration = 0
            consecutive_like_misses = 0
            while amount_liked < amount:
                iteration += 1
                if iteration > max_iterations:
                    print(
                        "Bucle de likes detenido: límite de iteraciones ({}) alcanzado. "
                        "Likes conseguidos: {}/{}.".format(max_iterations, amount_liked, amount)
                    )
                    break
                t0 = time.time()
                saved_name = saved_age = None
                geomatch = None
                do_like = True
                if randomize_sleep:
                    sleep = random.uniform(0.2, 0.6) * initial_sleep

                # Comportamiento humano: abrir perfil y pasar fotos antes de decidir (si no usamos filtros)
                if not use_filters and browse_before_like > 0:
                    self._adapter.open_profile_and_browse_photos(browse_before_like, browse_photos_delay)
                    self._adapter.close_profile()

                if use_filters:
                    try:
                        geomatch = self.get_geomatch(quickload=True, browse_photos=browse_photos, browse_photos_delay=browse_photos_delay)
                        rejected, reason = should_reject_profile(
                            geomatch, reject_keywords, reject_if_male,
                            reject_profile_emojis, reject_nonbinary_pronouns
                        )
                        saved_name = (geomatch.get_name() or "").strip() or "—"
                        saved_age = geomatch.get_age()
                        if rejected:
                            do_like = False
                            print("  Descartado Filtro: {}".format(reason))
                        else:
                            # Filtro de modelo de preferencias (foto)
                            if _photo_model is not None and not rejected:
                                urls = geomatch.get_image_urls() or []
                                if urls:
                                    liked_by_model, score = _photo_model.predict_from_url(
                                        urls[0], threshold=photo_model_threshold
                                    )
                                    if not liked_by_model:
                                        rejected = True
                                        reason = "Modelo foto (score={:.2f})".format(score)
                                        do_like = False
                                        print("  Descartado Modelo: score={:.2f}".format(score))
                            if not rejected:
                                if saved_age is not None:
                                    print("  Filtro OK | {} | {}".format(saved_name, saved_age))
                                else:
                                    print("  Filtro OK | {}".format(saved_name))
                    except Exception as e:
                        do_like = False
                        print("  Error leyendo perfil: {}".format(str(e)[:60]))
                        saved_name = saved_age = None
                        geomatch = None

                if use_filters:
                    self._adapter.close_profile()
                if do_like and random.random() <= ratio:
                    if self._adapter.like():
                        amount_liked += 1
                        self.session_data['like'] += 1
                        consecutive_like_misses = 0
                        elapsed = time.time() - t0
                        name_str = saved_name if use_filters else ((geomatch.get_name() if geomatch else None) or "—")
                        name_str = str(name_str).strip() if name_str else "—"
                        age_val = saved_age if use_filters else (geomatch.get_age() if geomatch else None)
                        age_str = str(age_val).strip() if age_val is not None and str(age_val).strip() else ""
                        if age_str:
                            print('Like {}/{} - "{}" {} - {:.1f}s'.format(amount_liked, amount, name_str, age_str, elapsed))
                        else:
                            print('Like {}/{} - "{}" - {:.1f}s'.format(amount_liked, amount, name_str, elapsed))
                        if save_liked_photos and geomatch:
                            self._save_liked_photos(geomatch, base_dir=liked_photos_dir, saved_name=saved_name, saved_age=saved_age)
                    else:
                        self.session_data['dislike'] += 1
                        consecutive_like_misses += 1
                else:
                    if not do_like or random.random() > ratio:
                        self._adapter.dislike()
                        self.session_data['dislike'] += 1
                    consecutive_like_misses = 0

                if consecutive_like_misses >= 15:
                    print(
                        "Bucle de likes detenido: demasiados likes fallidos seguidos ({}). "
                        "Likes conseguidos: {}/{}.".format(consecutive_like_misses, amount_liked, amount)
                    )
                    break

                time.sleep(sleep)

            self._print_liked_stats()

    def collect_training_data(self, n: int = 100, save_dir: str = 'data/training'):
        """
        Modo interactivo de recopilación de datos para el modelo de preferencias.

        Muestra cada perfil en el terminal y espera que el usuario pulse:
          [y] → like (foto guardada en save_dir/liked/)
          [n] → dislike (foto guardada en save_dir/disliked/)
          [q] → salir

        Una vez recogidos suficientes ejemplos, llama a train_preference_model()
        y usa session.like(photo_model_threshold=0.4) para automatizar.
        """
        if not self._is_logged_in():
            return
        import requests as _requests
        from pathlib import Path as _Path

        liked_dir = _Path(save_dir) / 'liked'
        disliked_dir = _Path(save_dir) / 'disliked'
        liked_dir.mkdir(parents=True, exist_ok=True)
        disliked_dir.mkdir(parents=True, exist_ok=True)

        collected = 0
        skipped = 0

        print("\n=== Recopilación de datos de entrenamiento ({} perfiles) ===".format(n))
        print("Controles: [y] Like  [n] Dislike  [q] Salir\n")

        while collected < n:
            self._handle_potential_popups()
            try:
                geomatch = self.get_geomatch(quickload=True, browse_photos=0)
                if geomatch is None:
                    skipped += 1
                    if skipped > 20:
                        print("Demasiados perfiles sin datos, deteniéndose.")
                        break
                    self._adapter.dislike()
                    time.sleep(1.0)
                    continue

                name = (geomatch.get_name() or "—").strip()
                age = geomatch.get_age()
                bio = (geomatch.get_bio() or "")
                image_urls = geomatch.get_image_urls() or []

                print("[{}/{}] {}, {}".format(collected + 1, n, name, age))
                if bio:
                    bio_preview = bio.replace("\n", " ")[:100]
                    print("  Bio: {}{}".format(bio_preview, "..." if len(bio) > 100 else ""))

                # Descargar primera foto
                img_bytes = None
                if image_urls:
                    try:
                        resp = _requests.get(image_urls[0], timeout=8)
                        if resp.status_code == 200:
                            img_bytes = resp.content
                    except Exception:
                        pass

                while True:
                    choice = input("  ¿Like? [y/n/q]: ").strip().lower()
                    if choice in ('y', 'n', 'q'):
                        break

                if choice == 'q':
                    print("Saliendo de la recopilación.")
                    break

                dest_dir = liked_dir if choice == 'y' else disliked_dir
                if img_bytes:
                    filename = "{}_{}_{}{}".format(
                        name.replace(" ", "_"), age or 0, collected + 1, '.jpg'
                    )
                    (dest_dir / filename).write_bytes(img_bytes)

                self._adapter.close_profile()
                if choice == 'y':
                    self._adapter.like()
                    self.session_data['like'] += 1
                else:
                    self._adapter.dislike()
                    self.session_data['dislike'] += 1

                collected += 1
                skipped = 0
                time.sleep(random.uniform(1.5, 3.0))

            except Exception as e:
                print("  Error: {}, saltando...".format(str(e)[:60]))
                skipped += 1
                try:
                    self._adapter.dislike()
                except Exception:
                    pass
                time.sleep(1.0)

        n_liked = len(list(liked_dir.glob('*.jpg')))
        n_disliked = len(list(disliked_dir.glob('*.jpg')))
        print("\n=== Recopilación completada: {} perfiles ===".format(collected))
        print("  Liked:    {} fotos → {}".format(n_liked, liked_dir))
        print("  Disliked: {} fotos → {}".format(n_disliked, disliked_dir))
        print("  Siguiente paso: session.train_preference_model()")

    def train_preference_model(self, training_dir: str = 'data/training', model_path: str = None):
        """
        Entrena el modelo de preferencias con los datos recogidos por collect_training_data().

        Requiere: scikit-learn (pip install scikit-learn)
                  torchvision (pip install torch torchvision)  ← recomendado
                  o deepface (ya en requirements.txt)           ← fallback

        Devuelve el diccionario de métricas o None si hay error.
        """
        kwargs = {'model_path': model_path} if model_path else {}
        model = PhotoPreferenceModel(**kwargs)

        print("\n=== Entrenando modelo de preferencias ===")
        print("  Datos: {}".format(training_dir))

        try:
            result = model.train(training_dir)
            print("  Liked:       {} fotos".format(result['n_liked']))
            print("  Disliked:    {} fotos".format(result['n_disliked']))
            print("  Total:       {} fotos".format(result['n_total']))
            print("  Accuracy CV: {:.1%}".format(result['accuracy']))
            print("  Modelo:      {}".format(model.model_path))
            print("\n  Uso: session.like(amount=500, photo_model_threshold=0.4)")
            return result
        except Exception as e:
            print("  Error entrenando: {}".format(e))
            return None

    def dislike(self, amount=1):
        if self._is_logged_in():
            for _ in range(amount):
                self._handle_potential_popups()
                self._adapter.dislike()
                self.session_data['dislike'] += 1
            self._print_liked_stats()

    def superlike(self, amount=1):
        if self._is_logged_in():
            for _ in range(amount):
                self._handle_potential_popups()
                self._adapter.superlike()
                self.session_data['superlike'] += 1
                time.sleep(1)
            self._print_liked_stats()

    def get_geomatch(self, quickload=True, browse_photos=1, browse_photos_delay=0.2):
        """browse_photos: 0 = no pasar fotos; 2 = pasar 2 fotos (comportamiento humano)."""
        if self._is_logged_in():
            self._handle_potential_popups()
            return self._adapter.get_current_profile(
                quickload=quickload, browse_photos=browse_photos, browse_photos_delay=browse_photos_delay
            )
        return None

    def get_chat_ids(self, new=True, messaged=True):
        if self._is_logged_in():
            self._handle_potential_popups()
            return self._adapter.get_chat_ids(new, messaged)
        return []

    def get_new_matches(self, amount=100000, quickload=True):
        if self._is_logged_in():
            self._handle_potential_popups()
            return self._adapter.get_new_matches(amount, quickload)
        return []

    def get_messaged_matches(self, amount=100000, quickload=True):
        if self._is_logged_in():
            self._handle_potential_popups()
            return self._adapter.get_messaged_matches(amount, quickload)
        return []

    def send_message(self, chatid, message):
        if self._is_logged_in():
            self._handle_potential_popups()
            self._adapter.send_message(chatid, message)

    def send_gif(self, chatid, gifname):
        if self._is_logged_in():
            self._handle_potential_popups()
            self._adapter.send_gif(chatid, gifname)

    def send_song(self, chatid, songname):
        if self._is_logged_in():
            self._handle_potential_popups()
            self._adapter.send_song(chatid, songname)

    def send_socials(self, chatid, media):
        if self._is_logged_in():
            self._handle_potential_popups()
            self._adapter.send_socials(chatid, media)

    def unmatch(self, chatid):
        if self._is_logged_in():
            self._handle_potential_popups()
            self._adapter.unmatch(chatid)

    # Utilities
    def _handle_potential_popups(self):
        result = self._adapter.handle_popups()
        if result == "POPUP: Dismissed NEW MATCH" and self.may_send_email and self.email:
            try:
                EmailHelper.send_mail_match_found(self.email)
            except Exception:
                print("Some error occurred when trying to send mail.")
        return result

    def _is_logged_in(self):
        return self._adapter.is_logged_in()

    def _get_msg_box(self, lines, indent=1, width=None, title=None):
        """Print message-box with optional title."""
        space = " " * indent
        if not width:
            width = max(map(len, lines))
        box = f'/{"=" * (width + indent * 2)}\\\n'  # upper_border
        if title:
            box += f'|{space}{title:<{width}}{space}|\n'  # title
            box += f'|{space}{"-" * len(title):<{width}}{space}|\n'  # underscore
        box += ''.join([f'|{space}{line:<{width}}{space}|\n' for line in lines])
        box += f'\\{"=" * (width + indent * 2)}/'  # lower_border
        return box

    def _print_liked_stats(self):
        """Muestra el resumen exacto de likes y dislikes de la sesión."""
        likes = self.session_data['like']
        dislikes = self.session_data['dislike']
        superlikes = self.session_data['superlike']
        print("--- Resumen ---")
        print("  Likes dados:    {}".format(likes))
        print("  Dislikes dados: {}".format(dislikes))
        print("  Superlikes:     {}".format(superlikes))
