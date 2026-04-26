import string
import random
import os
import json
import time

import urllib.request
from PIL import Image
import hashlib


class StorageHelper:

    @staticmethod
    def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    # Returns hash value of the image saved by the url given. Si hash en exclude_hashes, no guarda y devuelve None.
    # custom_filename: si se pasa (ej. "Amanda-27"), guarda como Amanda-27.jpg; si existe, Amanda-27_2.jpg, etc.
    @staticmethod
    def store_image_as(url, directory, amount_of_attempts=1, exclude_hashes=None, custom_filename=None):
        full_dir = os.path.join(os.getcwd(), directory) if not os.path.isabs(directory) else directory
        full_dir = os.path.normpath(full_dir)
        if not os.path.exists(full_dir):
            os.makedirs(full_dir)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        try:
            request_ = urllib.request.Request(url, None, headers)
            response = urllib.request.urlopen(request_, timeout=15)
            data = response.read()
        except Exception as e:
            if amount_of_attempts < 5:
                time.sleep(amount_of_attempts * 2)
                return StorageHelper.store_image_as(url, directory, amount_of_attempts + 1)
            print("  [store_image] Error descargando: {}".format(str(e)[:60]))
            return None

        temp_name = "temporary"
        temp_jpg = os.path.join(full_dir, temp_name + ".jpg")

        try:
            if ".jpg" in url.lower() or "jpeg" in url.lower():
                with open(temp_jpg, 'wb') as f:
                    f.write(data)
            elif '.webp' in url.lower():
                temp_webp = os.path.join(os.getcwd(), temp_name + ".webp")
                with open(temp_webp, 'wb') as f:
                    f.write(data)
                im = Image.open(temp_webp).convert("RGB")
                im.save(temp_jpg, "jpeg")
                try:
                    os.remove(temp_webp)
                except Exception:
                    pass
            else:
                with open(temp_jpg, 'wb') as f:
                    f.write(data)
                try:
                    im = Image.open(temp_jpg)
                    im.verify()
                except Exception:
                    try:
                        im = Image.open(temp_jpg)
                        im.load()
                    except Exception:
                        pass
        except Exception as e:
            print("  [store_image] Error guardando: {}".format(str(e)[:60]))
            return None

        try:
            im = Image.open(temp_jpg)
            hashvalue = hashlib.md5(im.tobytes()).hexdigest()
            if exclude_hashes and hashvalue in exclude_hashes:
                try:
                    os.remove(temp_jpg)
                except Exception:
                    pass
                return None
            if custom_filename:
                safe = "".join(c for c in custom_filename if c not in r'\/:*?"<>|').strip().rstrip(" .") or "perfil"
                base_path = os.path.join(full_dir, safe + ".jpg")
                final_path = base_path
                n = 2
                while os.path.isfile(final_path):
                    final_path = os.path.join(full_dir, "{}_{}.jpg".format(safe, n))
                    n += 1
            else:
                final_path = os.path.join(full_dir, hashvalue + ".jpg")
            if not os.path.isfile(final_path):
                os.rename(temp_jpg, final_path)
            else:
                try:
                    os.remove(temp_jpg)
                except Exception:
                    pass
            return hashvalue
        except Exception as e:
            if os.path.isfile(temp_jpg):
                try:
                    hashvalue = hashlib.md5(open(temp_jpg, 'rb').read()).hexdigest()
                    if exclude_hashes and hashvalue in exclude_hashes:
                        try:
                            os.remove(temp_jpg)
                        except Exception:
                            pass
                        return None
                    if custom_filename:
                        safe = "".join(c for c in custom_filename if c not in r'\/:*?"<>|').strip().rstrip(" .") or "perfil"
                        base_path = os.path.join(full_dir, safe + ".jpg")
                        final_path = base_path
                        n = 2
                        while os.path.isfile(final_path):
                            final_path = os.path.join(full_dir, "{}_{}.jpg".format(safe, n))
                            n += 1
                    else:
                        final_path = os.path.join(full_dir, hashvalue + ".jpg")
                    if not os.path.isfile(final_path):
                        os.rename(temp_jpg, final_path)
                    return hashvalue
                except Exception:
                    pass
            print("  [store_image] Error renombrando: {}".format(str(e)[:50]))
            return None

    @staticmethod
    def store_match(match, directory, filename):
        if not os.path.exists(directory):
            os.makedirs(directory)

        filepath = directory + "/{}.json".format(filename)

        try:
            with open(filepath, "r", encoding='utf-8') as fp:
                data = json.load(fp)
        except IOError:
            print("Could not read file, starting from scratch")
            data = {}

        data[match.get_id()] = match.get_dictionary()

        with open(filepath, 'w+', encoding="utf-8") as file:
            json.dump(data, file)
