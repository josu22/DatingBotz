from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import *
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import re
from tinderbotz.helpers.xpaths import content

# Panel de detalle del perfil (debajo de la foto): bio, filas, secciones
_PROFILE_BODY_XPATH = f'{content}/div/div[1]/div/main/div[1]/div/div/div[1]/div[1]/div/div[2]'
from datetime import datetime

from core.selenium_retry import run_webdriver_action

class GeomatchHelper:

    delay = 1.0  # tiempo máximo de espera para elementos (reducido para likes más rápidos)
    HOME_URL = "https://www.tinder.com/app/recs"

    @staticmethod
    def _is_on_app_page(browser):
        """True si estamos en cualquier sección de la app (recs, explore, etc.) donde se pueden dar likes."""
        url = (browser.current_url or "").strip()
        return "tinder.com/app/" in url

    def __init__(self, browser):
        self.browser = browser
        # No redirigir si ya estamos en la app (recs, explore, etc.); así se pueden dar likes en cualquier sección
        if not self._is_on_app_page(self.browser):
            self._get_home_page()

    def like(self)->bool:
        try:
            def _send_like():
                ActionChains(self.browser).send_keys(Keys.ARROW_RIGHT).perform()

            run_webdriver_action(_send_like, retries=2, delay=0.35)
            return True

        except (TimeoutException, ElementClickInterceptedException):
            if not self._is_on_app_page(self.browser):
                self._get_home_page()
            return False
        except WebDriverException:
            return False

    def dislike(self):
        try:
            def _send_dislike():
                ActionChains(self.browser).send_keys(Keys.ARROW_LEFT).perform()

            run_webdriver_action(_send_dislike, retries=2, delay=0.35)
        except (TimeoutException, ElementClickInterceptedException):
            if not self._is_on_app_page(self.browser):
                self._get_home_page()
        except WebDriverException:
            pass

    def superlike(self):
        try:
            if 'profile' in self.browser.current_url:
                xpath = f'{content}/div/div[1]/div/main/div[1]/div/div/div[1]/div[2]/div/div/div[3]/div/div/div/button'

                def _click_super():
                    WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located(
                        (By.XPATH, xpath)))
                    self.browser.find_element(By.XPATH, xpath).click()

                run_webdriver_action(_click_super, retries=2, delay=0.35)

            else:
                xpath = f'{content}/div/div[1]/div/main/div[1]/div/div/div[1]'

                def _drag_super():
                    WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located(
                        (By.XPATH, xpath)))
                    card = self.browser.find_element(By.XPATH, xpath)
                    ActionChains(self.browser).drag_and_drop_by_offset(card, 0, -200).perform()

                run_webdriver_action(_drag_super, retries=2, delay=0.35)

            time.sleep(1)

        except (TimeoutException, ElementClickInterceptedException):
            if not self._is_on_app_page(self.browser):
                self._get_home_page()
        except WebDriverException:
            if not self._is_on_app_page(self.browser):
                self._get_home_page()

    def open_profile(self, second_try=False):
        """Abre la vista de perfil de la carta actual (tecla arriba)."""
        self._open_profile(second_try)

    def _open_profile(self, second_try=False):
        if self._is_profile_opened(): return;
        try:
            #xpath = '//button'
            #WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located(
            #    (By.XPATH, xpath)))
            #buttons = self.browser.find_elements(By.XPATH, xpath)

            #for button in buttons:
            #    # some buttons might not have a span as subelement
            #    try:
            #        text_span = button.find_element(By.XPATH, './/span').text
            #        if 'open profile' in text_span.lower():
            #            button.click()
            #            break
            #    except:
            #        continue

            # New Implementation
            action = ActionChains(self.browser)
            action.send_keys(Keys.ARROW_UP).perform()

            #time.sleep(1)

        except (ElementClickInterceptedException, TimeoutException):
            if not second_try:
                print("Trying again to locate the profile info button in a few seconds")
                time.sleep(1)
                self._open_profile(second_try=True)
            else:
                self.browser.refresh()
        except:
            self.browser.get(self.HOME_URL)
            if not second_try:
                self._open_profile(second_try=True)

    def close_profile(self):
        """Vuelve de la vista de perfil a la carta (recs) para poder dar like/dislike correctamente."""
        if not self._is_profile_opened():
            return
        try:
            action = ActionChains(self.browser)
            action.send_keys(Keys.ARROW_DOWN).perform()
            time.sleep(0.15)
        except Exception:
            pass

    def browse_photos(self, num_photos=1, delay_between=0.10):
        """Comportamiento humano: pasa varias fotos del perfil con una breve pausa entre ellas."""
        if not self._is_profile_opened():
            return
        try:
            bullets = self.browser.find_elements(By.CLASS_NAME, "bullet")
            if len(bullets) <= 1:
                return
            n = min(num_photos, len(bullets) - 1)
            for i in range(n):
                try:
                    bullets[i + 1].click()
                    time.sleep(delay_between)
                except (StaleElementReferenceException, Exception):
                    break
        except Exception:
            pass

    @staticmethod
    def _parse_name_age(text):
        """Parsea 'Rebecca 24' o 'Carlota27' en (nombre, edad). Devuelve (name, age) con age int o None."""
        if not text or not (text or "").strip():
            return (None, None)
        text = text.strip()
        # Con espacio: "Nombre 24"
        m = re.match(r"^(.+?)\s+(\d{1,3})\s*$", text)
        if m:
            return (m.group(1).strip(), int(m.group(2)))
        # Sin espacio: "Carlota27" -> nombre sin dígitos + edad al final
        m = re.match(r"^([^\d]+?)(\d{1,3})\s*$", text)
        if m:
            return (m.group(1).strip(), int(m.group(2)))
        return (text, None)

    def _get_name_age_fallback(self):
        """Obtiene nombre y edad desde un único elemento (ej. 'Rebecca 24' o 'Carlota27'). Devuelve (name, age) o (None, None)."""
        try:
            for xpath in ["//main//h1", "//h1", f"{content}//h1"]:
                try:
                    el = self.browser.find_element(By.XPATH, xpath)
                    text = (el.text or "").strip()
                    if not text:
                        continue
                    return self._parse_name_age(text)
                except Exception:
                    continue
        except Exception:
            pass
        return (None, None)

    def get_name(self):
        if not self._is_profile_opened():
            self._open_profile()

        name = None
        try:
            xpath = f'{content}/div/div[1]/div/main/div[1]/div/div/div[1]/div[1]/div/div[2]/div[1]/div/div[1]/div/h1'
            WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, xpath)))
            element = self.browser.find_element(By.XPATH, xpath)
            raw = (element.text or "").strip()
            name, _ = self._parse_name_age(raw)
            name = name or raw
        except Exception:
            pass
        if not name:
            name, _ = self._get_name_age_fallback()
        return name

    def get_age(self):
        if not self._is_profile_opened():
            self._open_profile()

        age = None
        try:
            xpath = f'{content}/div/div[1]/div/main/div[1]/div/div/div[1]/div[1]/div/div[2]/div[1]/div/div[1]/span'
            WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, xpath)))
            element = self.browser.find_element(By.XPATH, xpath)
            age = int(element.text)
        except Exception:
            pass
        if age is None:
            _, age = self._get_name_age_fallback()
        return age

    def is_verified(self):
        if not self._is_profile_opened():
            self._open_profile()

        xpath_badge = f'{content}/div/div[1]/div/main/div[1]/div/div/div[1]/div[1]/div/div[2]/div[1]/div/div[1]/div[2]'
        try:
            self.browser.find_element(By.XPATH, xpath_badge)
            return True

        except:
            return False

    _WORK_SVG_PATH = "M7.15 3.434h5.7V1.452a.728.728 0 0 0-.724-.732H7.874a.737.737 0 0 0-.725.732v1.982z"
    _STUDYING_SVG_PATH = "M11.87 5.026L2.186 9.242c-.25.116-.25.589 0 .705l.474.204v2.622a.78.78 0 0 0-.344.657c0 .42.313.767.69.767.378 0 .692-.348.692-.767a.78.78 0 0 0-.345-.657v-2.322l2.097.921a.42.42 0 0 0-.022.144v3.83c0 .45.27.801.626 1.101.358.302.842.572 1.428.804 1.172.46 2.755.776 4.516.776 1.763 0 3.346-.317 4.518-.777.586-.23 1.07-.501 1.428-.803.355-.3.626-.65.626-1.1v-3.83a.456.456 0 0 0-.022-.145l3.264-1.425c.25-.116.25-.59 0-.705L12.13 5.025c-.082-.046-.22-.017-.26 0v.001zm.13.767l8.743 3.804L12 13.392 3.257 9.599l8.742-3.806zm-5.88 5.865l5.75 2.502a.319.319 0 0 0 .26 0l5.75-2.502v3.687c0 .077-.087.262-.358.491-.372.29-.788.52-1.232.68-1.078.426-2.604.743-4.29.743s-3.212-.317-4.29-.742c-.444-.161-.86-.39-1.232-.68-.273-.23-.358-.415-.358-.492v-3.687z"
    _HOME_SVG_PATH = "M19.695 9.518H4.427V21.15h15.268V9.52zM3.109 9.482h17.933L12.06 3.709 3.11 9.482z"
    _LOCATION_SVG_PATH = "M11.436 21.17l-.185-.165a35.36 35.36 0 0 1-3.615-3.801C5.222 14.244 4 11.658 4 9.524 4 5.305 7.267 2 11.436 2c4.168 0 7.437 3.305 7.437 7.524 0 4.903-6.953 11.214-7.237 11.48l-.2.167zm0-18.683c-3.869 0-6.9 3.091-6.9 7.037 0 4.401 5.771 9.927 6.897 10.972 1.12-1.054 6.902-6.694 6.902-10.95.001-3.968-3.03-7.059-6.9-7.059h.001z"
    _LOCATION_SVG_PATH_2 = "M11.445 12.5a2.945 2.945 0 0 1-2.721-1.855 3.04 3.04 0 0 1 .641-3.269 2.905 2.905 0 0 1 3.213-.645 3.003 3.003 0 0 1 1.813 2.776c-.006 1.653-1.322 2.991-2.946 2.993zm0-5.544c-1.378 0-2.496 1.139-2.498 2.542 0 1.404 1.115 2.544 2.495 2.546a2.52 2.52 0 0 0 2.502-2.535 2.527 2.527 0 0 0-2.499-2.545v-.008z"
    _GENDER_SVG_PATH = "M15.507 13.032c1.14-.952 1.862-2.656 1.862-5.592C17.37 4.436 14.9 2 11.855 2 8.81 2 6.34 4.436 6.34 7.44c0 3.07.786 4.8 2.02 5.726-2.586 1.768-5.054 4.62-4.18 6.204 1.88 3.406 14.28 3.606 15.726 0 .686-1.71-1.828-4.608-4.4-6.338"

    @staticmethod
    def _normalize_svg_path(d):
        """Normaliza el path del SVG para comparar aunque cambie espaciado/decimales."""
        if not d:
            return ""
        return " ".join(d.split())

    def _get_gender_fallback_from_profile_text(self):
        """
        Fallback de género: solo confirma FEMENINO a partir del texto visible.
        NO infiere masculino desde el texto libre porque la bio puede mencionar
        a otra persona ('busco un hombre', 'me gustan los chicos') y causaría
        falsos positivos rechazando perfiles de mujeres.
        """
        _female_words = ("woman", "women", "mujer", "female", "chica", "femme",
                         "mulher", "donna", "femenino", "chicas")
        try:
            profile_xpath = f'{content}/div/div[1]/div/main/div[1]/div/div/div[1]/div[1]/div/div[2]'
            el = self.browser.find_element(By.XPATH, profile_xpath)
            text = (el.text or "").lower()
            for word in _female_words:
                if word in text:
                    return word.capitalize()
        except Exception:
            pass
        try:
            el = self.browser.find_element(By.TAG_NAME, "main")
            text = (el.text or "").lower()
            for word in _female_words:
                if word in text:
                    return word.capitalize()
        except Exception:
            pass
        return None

    # Keywords de género para el fallback por texto exacto de Row
    _MALE_GENDER_EXACT = frozenset({
        "man", "men", "hombre", "male", "chico", "homme", "homem",
        "masculino", "boy", "uomo", "männlich", "macho",
    })
    _FEMALE_GENDER_EXACT = frozenset({
        "woman", "women", "mujer", "female", "chica", "femme", "mulher",
        "donna", "femenino", "weiblich", "girl", "chicas",
    })

    def _get_gender_from_rows_exact_text(self, rows) -> str | None:
        """
        Fallback 1: recorre los Row ya leídos y compara el texto de div[2] exactamente
        contra keywords de género. El texto de un Row de género es siempre una sola palabra
        ("Man", "Woman", "Hombre"...), lo que lo diferencia de trabajo/estudios/ciudad.
        Es seguro porque no lee la bio libre.
        """
        for row in rows:
            try:
                value_el = row.find_element(By.XPATH, ".//div[2]")
                text = (value_el.text or "").strip().lower()
                if not text or len(text) > 20:
                    continue
                if text in self._FEMALE_GENDER_EXACT:
                    return text.capitalize()
                if text in self._MALE_GENDER_EXACT:
                    return text.capitalize()
            except Exception:
                continue
        return None

    def get_row_data(self):
        """
        Lee los datos de las filas (Row) del perfil: trabajo, estudios, casa, GÉNERO, distancia.
        GÉNERO: texto del segundo div (div[2]) de la fila cuyo icono SVG es el de género.
        Ese texto es el que muestra Tinder: "Man", "Woman", "Hombre", "Mujer", etc.
        """
        if not self._is_profile_opened():
            self._open_profile()

        rowdata = {}
        xpath = '//div[@class="Row"]'
        rows = self.browser.find_elements(By.XPATH, xpath)
        norm_gender = self._normalize_svg_path(self._GENDER_SVG_PATH)
        norm_work = self._normalize_svg_path(self._WORK_SVG_PATH)
        norm_study = self._normalize_svg_path(self._STUDYING_SVG_PATH)
        norm_home = self._normalize_svg_path(self._HOME_SVG_PATH)
        norm_loc = self._normalize_svg_path(self._LOCATION_SVG_PATH)
        norm_loc2 = self._normalize_svg_path(self._LOCATION_SVG_PATH_2)

        for row in rows:
            try:
                svg_el = row.find_element(By.XPATH, ".//*[starts-with(@d, 'M')]")
                svg = self._normalize_svg_path(svg_el.get_attribute('d'))
                value_el = row.find_element(By.XPATH, ".//div[2]")
                value = (value_el.text or "").strip()
            except Exception:
                continue
            if svg == norm_work:
                rowdata['work'] = value
            if svg == norm_study:
                rowdata['study'] = value
            if svg == norm_home:
                rowdata['home'] = value.split(' ')[-1] if value else None
            if svg == norm_gender and value:
                rowdata.setdefault('genders', []).append(value)
            if svg == norm_loc or svg == norm_loc2:
                distance = value.split(' ')[0] if value else None
                try:
                    distance = int(distance) if distance else None
                except (TypeError, ValueError):
                    distance = 1 if value and "less" in value.lower() else None
                rowdata['distance'] = distance

        # Fallback 1: leer texto exacto de los Row sin depender del SVG
        # (cubre el caso en que Tinder cambia el path del icono de género)
        if 'genders' not in rowdata or not rowdata['genders']:
            row_gender = self._get_gender_from_rows_exact_text(rows)
            if row_gender:
                rowdata.setdefault('genders', []).append(row_gender)

        # Fallback 2: texto visible del panel (solo confirma femenino — ver método)
        if 'genders' not in rowdata or not rowdata['genders']:
            fallback = self._get_gender_fallback_from_profile_text()
            if fallback:
                rowdata.setdefault('genders', []).append(fallback)

        if 'genders' in rowdata:
            rowdata['gender'] = rowdata['genders'][0] if len(rowdata['genders']) == 1 else None
        return rowdata

    def _scroll_profile_panel_for_bio(self):
        """Baja el scroll del perfil para que la descripción y secciones carguen (Tinder SPA)."""
        try:
            panel = self.browser.find_element(By.XPATH, _PROFILE_BODY_XPATH)
            self.browser.execute_script(
                """
                var el = arguments[0];
                for (var i = 0; i < 8 && el; i++) {
                    if (el.scrollHeight > el.clientHeight + 30) {
                        el.scrollTop = Math.min(el.scrollTop + 480, el.scrollHeight);
                        break;
                    }
                    el = el.parentElement;
                }
                """,
                panel,
            )
        except Exception:
            pass
        for _ in range(10):
            try:
                ActionChains(self.browser).send_keys(Keys.ARROW_DOWN).perform()
            except Exception:
                break
            time.sleep(0.07)
        time.sleep(0.2)

    def _get_profile_body_inner_text(self):
        """Texto visible completo del panel del perfil (bio + filas + pasiones); robusto si cambian clases CSS."""
        for xpath in (_PROFILE_BODY_XPATH, "//main"):
            try:
                el = self.browser.find_element(By.XPATH, xpath)
                t = (el.get_attribute("innerText") or el.text or "").strip()
                if t and len(t) > 5:
                    return t
            except Exception:
                continue
        return ""

    def get_bio_and_passions(self):
        if not self._is_profile_opened():
            self._open_profile()

        time.sleep(0.2)
        self._scroll_profile_panel_for_bio()

        bio = None
        looking_for = None

        infoItems = {
            "passions": [],
            "lifestyle": [],
            "basics": []
        }

        anthem = None

        lifestyle = []

        # Bio: selectores actuales de Tinder + fallbacks por clase parcial
        try:
            bio = self.browser.find_element(By.CSS_SELECTOR, 'div[class*="Px(16px) Py(12px) Us(t)"').text
        except Exception:
            pass
        if not bio or not (bio or "").strip():
            try:
                for sel in [
                    'div[class*="Px(16px) Py(12px) Us(t)"]',
                    'div[class*="Px(16px)"][class*="Py(12px)"][class*="Us(t)"]',
                    'div[class*="breakWords"][class*="Us(t)"]',
                    'span[class*="Typs(body-1-regular)"]',
                    'div[class*="Typs(body-1-regular)"]',
                    "main div[class*='Us(t)']",
                    "div[class*='Typs(body)']",
                ]:
                    try:
                        for el in self.browser.find_elements(By.CSS_SELECTOR, sel):
                            t = (el.get_attribute("innerText") or el.text or "").strip()
                            if t and 2 <= len(t) < 4000:
                                bio = t
                                break
                        if bio:
                            break
                    except Exception:
                        continue
            except Exception:
                pass

        # Texto del panel completo: incluye descripción aunque cambien las clases del bloque "About"
        body_dump = self._get_profile_body_inner_text()
        specific = (bio or "").strip()
        if body_dump.strip():
            bio = body_dump.strip()
        elif specific:
            bio = specific
        else:
            bio = None

        # Looking for
        try:
            looking_for_el = self.browser.find_element(By.CSS_SELECTOR, 'div[class="Px(16px) My(12px)"]>div[class="D(b)"]')
            looking_for = looking_for_el.find_element(By.CSS_SELECTOR, 'div[class="Typs(subheading-1) CenterAlign"]').text

        except Exception as e:
            pass

        # Basics, Lifestyle and Passions
        try:
            sections = self.browser.find_elements(By.CSS_SELECTOR, "div[class='Px(16px) Py(12px)']")
            for section in sections:
                headline = section.find_element(By.TAG_NAME, "h2").text.lower()
                
                if headline in infoItems.keys():
                    infoElements = section.find_elements(By.CSS_SELECTOR, "div[class^='Bdrs(100px)']")
                    for infoElement in infoElements:
                        infoItems[headline].append(infoElement.text)
                elif headline == 'my anthem':
                    song = section.find_element(By.CSS_SELECTOR, "div[class$='C($c-ds-text-primary)']").text
                    artist = section.find_element(By.CSS_SELECTOR, "div[class$='C($c-ds-text-secondary)']").text
                    anthem = {
                        "song": song,
                        "artist": artist
                    }
                else:
                    print("Unknown Sect Headline:", headline)


            #if ('Passions' in passions_el.find_element(By.TAG_NAME, "h2").text):
            #    #print("Passions Text", passions_el.text)
            #    elements = passions_el.find_element(By.TAG_NAME, 'div').find_element(By.TAG_NAME, 'div').find_elements(By.TAG_NAME, 'div')
            #    for el in elements:
            #        passions.append(el.text)
        except Exception as e:
            pass

        return bio, infoItems["passions"], infoItems["lifestyle"], infoItems["basics"], anthem, looking_for

    @staticmethod
    def _extract_url_from_style(style_str):
        """
        Extrae la URL de background-image del atributo style.
        Tinder usa: style="background-image: url(&quot;https://images-ssl.gotinder.com/...&quot;); ..."
        """
        if not style_str or 'background-image' not in style_str:
            return None
        # url(&quot;https://...&quot;) o url("https://..."); la URL puede contener & y =
        for pattern in [
            r'url\s*\(\s*&quot;\s*(https://[^&]*?(?:&(?!quot;)[^&]*)*)\s*&quot;\s*\)',
            r'url\s*\(\s*&quot;\s*(https://.+?)\s*&quot;\s*\)',
            r'url\s*\(\s*["\'](https://[^"\']+)["\']\s*\)',
        ]:
            m = re.search(pattern, style_str, re.IGNORECASE)
            if m:
                url = m.group(1).strip()
                if url.startswith('http'):
                    return url
        # Fallback: buscar https:// en el style y tomar hasta el siguiente &quot; o "
        idx = style_str.find('https://')
        if idx != -1:
            end = style_str.find('&quot;', idx)
            if end == -1:
                end = style_str.find('"', idx)
            if end != -1:
                return style_str[idx:end].strip()
        return None

    def _extract_image_url_from_element(self, element):
        """Extrae la URL de la imagen: primero del atributo style (url(&quot;...&quot;)), luego de background-image."""
        try:
            style = element.get_attribute('style')
            if style:
                u = self._extract_url_from_style(style)
                if u:
                    return u
            bg = element.value_of_css_property('background-image') or ''
            if not bg or bg == 'none':
                return None
            for sep in ('"', "'"):
                if sep in bg:
                    parts = bg.split(sep)
                    if len(parts) >= 2 and parts[1].strip().startswith('http'):
                        return parts[1].strip()
            return None
        except Exception:
            return None

    def get_image_urls(self, quickload=True):
        """Solo imágenes del perfil actual: buscar únicamente dentro del panel del perfil abierto."""
        if not self._is_profile_opened():
            self._open_profile()

        image_urls = []
        # Contenedor del perfil abierto (evitar coger la foto de la siguiente carta)
        profile_container_xpath = f"{content}/div/div[1]/div/main/div[1]/div/div/div[1]/div[1]"
        slider_xpath = "//div[@aria-label='Profile slider']"

        def collect_from_container(container_el):
            urls = []
            for el in container_el.find_elements(By.XPATH, ".//div[@aria-label='Profile slider']"):
                u = self._extract_image_url_from_element(el)
                if u:
                    return [u]
                for child in el.find_elements(By.XPATH, ".//*[contains(@style, 'background-image') or contains(@style, '&quot;')]"):
                    u = self._extract_image_url_from_element(child)
                    if not u and child.get_attribute('style'):
                        u = self._extract_url_from_style(child.get_attribute('style'))
                    if u and "gotinder.com" in u:
                        return [u]
            return urls

        def collect_visible_urls():
            try:
                container = self.browser.find_element(By.XPATH, profile_container_xpath)
                return collect_from_container(container)
            except Exception:
                pass
            urls = []
            for el in self.browser.find_elements(By.XPATH, slider_xpath):
                u = self._extract_image_url_from_element(el)
                if u:
                    urls.append(u)
                    return urls
                for child in el.find_elements(By.XPATH, ".//*[contains(@style, 'background-image') or contains(@style, '&quot;')]"):
                    u = self._extract_image_url_from_element(child)
                    if not u and child.get_attribute('style'):
                        u = self._extract_url_from_style(child.get_attribute('style'))
                    if u and u not in urls and "gotinder.com" in u:
                        urls.append(u)
                        return urls
            return urls

        image_urls = collect_visible_urls()
        if not image_urls:
            time.sleep(0.15)
            image_urls = collect_visible_urls()
        # Fallback solo dentro del contenedor del perfil (no buscar en todo el DOM)
        if not image_urls:
            try:
                container = self.browser.find_element(By.XPATH, profile_container_xpath)
                candidates = []
                for el in container.find_elements(By.XPATH, ".//*[contains(@style, 'background-image') and contains(@style, 'gotinder.com')]"):
                    style = el.get_attribute('style')
                    u = self._extract_url_from_style(style)
                    if u:
                        try:
                            w, h = el.size.get('width', 0), el.size.get('height', 0)
                            candidates.append((w * h, u))
                        except Exception:
                            candidates.append((0, u))
                if candidates:
                    candidates.sort(key=lambda x: -x[0])
                    image_urls.append(candidates[0][1])
            except Exception:
                pass
        if not image_urls:
            try:
                container = self.browser.find_element(By.XPATH, profile_container_xpath)
                for el in container.find_elements(By.XPATH, ".//*[contains(@style, '&quot;')]"):
                    style = el.get_attribute('style')
                    u = self._extract_url_from_style(style)
                    if u and 'gotinder.com' in u:
                        image_urls.append(u)
                        break
            except Exception:
                pass

        # Con quickload, si no hay suficientes fotos, pasar por los bullets para recoger todas las URLs
        if quickload and len(image_urls) < 2:
            try:
                WebDriverWait(self.browser, self.delay).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "bullet")))
                n_bullets = len(self.browser.find_elements(By.CLASS_NAME, "bullet"))
                for i in range(min(n_bullets, 6)):
                    try:
                        btns = self.browser.find_elements(By.CLASS_NAME, "bullet")
                        if i >= len(btns):
                            break
                        btns[i].click()
                        time.sleep(0.25)
                        for el in self.browser.find_elements(By.XPATH, slider_xpath):
                            u = self._extract_image_url_from_element(el)
                            if u and u not in image_urls:
                                image_urls.append(u)
                    except (StaleElementReferenceException, IndexError):
                        break
            except TimeoutException:
                pass
            except Exception:
                pass
        if quickload:
            return image_urls

        try:
            classname = 'bullet'
            WebDriverWait(self.browser, self.delay).until(
                EC.presence_of_element_located((By.CLASS_NAME, classname)))
            image_btns = self.browser.find_elements(By.CLASS_NAME, classname)
            for btn in image_btns:
                btn.click()
                time.sleep(1)
                for el in self.browser.find_elements(By.XPATH, slider_xpath):
                    u = self._extract_image_url_from_element(el)
                    if u and u not in image_urls:
                        image_urls.append(u)
        except StaleElementReferenceException:
            pass
        except TimeoutException:
            try:
                for el in self.browser.find_elements(By.XPATH, slider_xpath):
                    u = self._extract_image_url_from_element(el)
                    if u and u not in image_urls:
                        image_urls.append(u)
            except Exception:
                pass
        except Exception:
            pass
        return image_urls

    @staticmethod
    def de_emojify(text):
        """Remove emojis from a string
        Args:
            text (string): string with emojis or not
        Returns:
            string: recompile string without emojis
        """
        regrex_pattern = re.compile(
            pattern="["
                    u"\U0001F600-\U0001F64F"  # emoticons
                    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                    u"\U0001F680-\U0001F6FF"  # transport & map symbols
                    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                    "]+",
            flags=re.UNICODE,
        )
        return regrex_pattern.sub(r'', text)

    def get_insta(self, text):
        """Take the bio and read line by line to match if the description
        contain an instagram user.
        Args:
            text (string): string with emojis or not
        Returns:
            ig (string): return valid instagram user.
        """
        if not text:
            return None
        valid_pattern = [
            "@",
            "ig-",
            "ig",
            "ig:",
            "ing",
            "ing:",
            "instag",
            "instag:",
            "insta:",
            "insta",
            "inst",
            "inst:",
            "instagram",
            "instagram:",
        ]
        description = text.rstrip().lower().strip()
        description = description.split()
        for x in range(len(description)):
            ig = self.de_emojify(description[x])
            if '@' in ig:
                return ig.replace('@', '')
            elif ig in valid_pattern:
                try:
                    if ':' in description[x + 1]:
                        return description[x + 2]
                    else:
                        return description[x + 1]
                except:
                    return None
            else:
                try:
                    ig = ig.split(':', 1)
                    if ig[0] in valid_pattern:
                        return ig[-1]
                except:
                    return None
        return None

    def _get_home_page(self):
        self.browser.get(self.HOME_URL)
        time.sleep(5)

    def _is_profile_opened(self):
        if '/profile' in self.browser.current_url:
            return True
        else:
            return False
