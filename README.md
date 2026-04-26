# DatingBotz

Automatización de Tinder y Bumble mediante Selenium. Scraping de perfiles, likes/dislikes automatizados con filtros avanzados, envío de mensajes y gestión de matches.

---

## Tabla de contenidos

- [Sobre el proyecto](#sobre-el-proyecto)
- [Tecnologías](#tecnologías)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Uso rápido](#uso-rápido)
  - [Tinder](#tinder)
  - [Bumble](#bumble)
- [Sistema de filtros](#sistema-de-filtros)
  - [Parámetros](#parámetros)
  - [Emojis detectados](#emojis-detectados)
  - [Detección de pronombres](#detección-de-pronombres)
  - [Lista de keywords por defecto](#lista-de-keywords-por-defecto)
  - [Personalizar el filtro](#personalizar-el-filtro)
- [Referencia de la API](#referencia-de-la-api)
- [Cómo evitar el baneo](#cómo-evitar-el-baneo)
- [Análisis de datos](#análisis-de-datos)
- [Aviso legal](#aviso-legal)

---

## Sobre el proyecto

DatingBotz automatiza las acciones más comunes en Tinder y Bumble:

- Abrir el navegador e iniciar sesión (Google, Facebook o SMS).
- Establecer una ubicación personalizada de forma gratuita (función de pago en Tinder Plus).
- Configurar preferencias: distancia, rango de edad, sexualidad.
- Dar likes y dislikes con ratio configurable y comportamiento humano (pausa, pasar fotos).
- **Filtrar perfiles** mediante palabras clave, emojis y pronombres antes de decidir.
- Scrapear datos de perfiles: nombre, edad, bio, imágenes, Instagram, pasiones…
- Enviar mensajes personalizados, GIFs, canciones y tarjetas de redes sociales.
- Recibir notificaciones por correo al obtener un match.

---

## Tecnologías

- [Python 3.x](https://www.python.org/)
- [Selenium](https://selenium.dev)
- [Undetected-Chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)
- [Pillow](https://python-pillow.org/) — procesado de imágenes
- [DeepFace](https://github.com/serengil/deepface) *(opcional)* — análisis de edad/género por IA

---

## Requisitos previos

- Python 3.8 o superior
- Google Chrome instalado
- Cuenta de Tinder o Bumble con login por Google, Facebook o SMS habilitado

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/DatingBotz.git
cd DatingBotz

# 2. Instalar dependencias
pip install -r requirements.txt
```

### Variables de entorno

No guardes credenciales en el código. Defínelas en el entorno antes de ejecutar:

```bash
# Tinder — Google / Facebook
export TINDER_EMAIL="tu@email.com"
export TINDER_PASSWORD="tu_contraseña"

# Tinder — SMS (opcional)
export TINDER_SMS_COUNTRY="+34"
export TINDER_SMS_PHONE="600000000"

# Bumble — SMS
export BUMBLE_SMS_COUNTRY="+34"
export BUMBLE_SMS_PHONE="600000000"

# Notificaciones por correo al hacer match (opcional)
export TINDERBOTZ_SMTP_USER="tu@gmail.com"
export TINDERBOTZ_SMTP_PASSWORD="app_password"
export TINDERBOTZ_SMTP_FROM="tu@gmail.com"
```

---

## Uso rápido

### Tinder

```python
# quickstart_tinder.py
from tinderbotz.session import Session
from tinderbotz.helpers.constants_helper import Sexuality
import os

session = Session()
session.login_using_google(
    os.environ["TINDER_EMAIL"],
    os.environ["TINDER_PASSWORD"]
)

# Dar 500 likes filtrando perfiles no deseados
session.like(
    amount=500,
    ratio="97.5%",          # probabilidad de dar like vs dislike
    sleep=2,                 # segundos entre swipes
    reject_if_male=True,     # descartar género masculino declarado
    reject_profile_emojis=True,          # descartar emojis trans / pride
    reject_nonbinary_pronouns=True,      # descartar they/them, ze/zir, etc.
    # reject_keywords=None → usa la lista por defecto (trans, gay, LGBTQ+)
    # reject_keywords=[]   → sin filtro de palabras clave
    save_liked_photos=True,
    browse_photos=3,
)

# Obtener matches nuevos y enviar mensaje
matches = session.get_new_matches(amount=10)
for match in matches:
    session.send_message(match.get_chat_id(), "Hola {}!".format(match.get_name()))
```

Ejecutar:
```bash
python quickstart_tinder.py
```

### Bumble

```python
# quickstart_bumble.py
from bumblebotz.session import Session
import os

session = Session()
session.login_using_sms(
    os.environ["BUMBLE_SMS_COUNTRY"],
    os.environ["BUMBLE_SMS_PHONE"]
)

session.like(
    amount=200,
    ratio="95%",
    sleep=6.0,
    reject_if_male=True,
    reject_profile_emojis=True,
    reject_nonbinary_pronouns=True,
)
```

---

## Sistema de filtros

El motor de filtrado está en [`core/profile_filters.py`](core/profile_filters.py) y es compartido por Tinder y Bumble.

Antes de dar like o dislike, el bot abre el perfil, extrae todo el texto disponible y aplica los filtros en este orden:

```
1. Emojis (trans flag, pride flag, rainbow, símbolos de género)
2. Pronombres no-binarios / trans (they/them, ze/zir, mixtos he+she)
3. Palabras clave (lista configurable)
4. Género declarado en la app (reject_if_male)
```

Los campos que se escanean son: **nombre, bio, busco, trabajo, estudios, ciudad, Instagram, himno, pasiones, lifestyle y basics**.

### Parámetros

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `reject_keywords` | `list \| None` | `None` | `None` = lista por defecto. `[]` = sin filtro de palabras. Lista propia = reemplaza la lista. |
| `reject_profile_emojis` | `bool` | `True` | Detectar emojis de trans flag, pride y símbolos de género. |
| `reject_nonbinary_pronouns` | `bool` | `True` | Detectar pronombres no-binarios y combinaciones trans (they/them, ze/zir, he+she…). |
| `reject_if_male` | `bool` | `True` | Rechazar si el género declarado en la app es masculino. |

### Emojis detectados

| Emoji | Descripción |
|---|---|
| 🏳️‍⚧️ | Trans flag (todas las variantes Unicode) |
| ⚧️ / ⚧ | Símbolo trans |
| 🏳️‍🌈 | Pride flag |
| 🌈 | Arcoíris (uso frecuente en perfiles LGBTQ+) |
| ⚢ | Símbolo lésbica |
| ⚣ | Símbolo gay |
| ⚥ | Símbolo intersex / bisexual |

La detección normaliza el texto con NFC y NFD para cubrir todas las variantes de codificación Unicode.

### Detección de pronombres

Los pronombres se declaran en el bio con el formato `pronombre/forma_objeto` y son uno de los indicadores más fiables en perfiles actuales.

**Pronombres no-binarios detectados:**

| Patrón | Ejemplo en bio |
|---|---|
| `they/them` | "they/them 🌈" |
| `ze/zir` | "ze/zir pronouns" |
| `xe/xem` | "call me xe/xem" |
| `fae/faer` | "fae/faer/faers" |
| `ey/em` | "ey/em/eir" |
| `ve/ver` | "ve/ver/vis" |
| `ne/nem` | "ne/nem/nir" |
| `per/pers` | "per/pers" |

**Pronombres mixtos (indicador trans):**

| Patrón | Ejemplo |
|---|---|
| `she/her he/him` | trans mujer |
| `he/him she/her` | trans hombre |

> `she/her` o `he/him` solos **no** activan el filtro porque son habituales en perfiles cis.

### Lista de keywords por defecto

`DEFAULT_REJECT_KEYWORDS_TRANS_GAY` contiene más de 120 términos organizados por categoría:

| Categoría | Ejemplos |
|---|---|
| Trans / crossdressing | `transgender`, `transsexual`, `transvestite`, `femboy`, `tgirl`, `travesti`, `mtf`, `ftm`, `m2f`, `f2m`… |
| No-binario / género no conforme | `non-binary`, `genderfluid`, `genderqueer`, `enby`, `agender`, `neutrois`, `bigender`, `pangender`, `androgyne`, `gnc`, `demiboy`, `demigirl`… |
| Transición médica | `hormone therapy`, `terapia hormonal`, `pre-op`, `post-op`, `amab`, `afab`… |
| Drag | `drag queen`, `drag king`, `drag performer`, `drag artist` |
| Gay / lésbica / LGBTQ+ | `gay`, `lesbian`, `lesbiana`, `pansexual`, `queer`, `sapphic`, `wlw`, `butch`, `stud`, `lgbt`, `lgbtq+`, `lgbtqia+`… |
| Alemán | `schwul`, `lesbisch`, `bisexuell`, `transgeschlechtlich`… |
| Francés | `lesbienne`, `bisexuel`, `bisexuelle`, `transgenre`… |
| Italiano | `lesbica`, `bisessuale`, `transessuale`… |
| Portugués | `lésbica`, `lésbicas`, `bissexual`… |

**Word-boundary:** las palabras cortas (≤4 caracteres) como `gay` o `trans` usan límites de palabra para evitar falsos positivos (`gayet`, `transport`, etc.).

### Personalizar el filtro

```python
# Añadir términos extra a la lista por defecto
from core.profile_filters import DEFAULT_REJECT_KEYWORDS_TRANS_GAY

mis_keywords = list(DEFAULT_REJECT_KEYWORDS_TRANS_GAY) + ["término_extra", "otro término"]
session.like(amount=100, reject_keywords=mis_keywords)

# Solo filtrar por emojis y pronombres, sin palabras clave
session.like(amount=100, reject_keywords=[], reject_profile_emojis=True, reject_nonbinary_pronouns=True)

# Sin ningún filtro de texto (solo género declarado en la app)
session.like(amount=100, reject_keywords=[], reject_profile_emojis=False, reject_nonbinary_pronouns=False, reject_if_male=True)

# Sin filtros en absoluto
session.like(amount=100, reject_keywords=[], reject_profile_emojis=False, reject_nonbinary_pronouns=False, reject_if_male=False)
```

---

## Referencia de la API

### `Session.like()`

```python
session.like(
    amount=500,                      # número de likes objetivo
    ratio="97.5%",                   # probabilidad de like vs dislike
    sleep=2,                         # segundos de pausa entre swipes
    randomize_sleep=True,            # aleatorizar el sleep (×0.2 a ×0.6)
    reject_keywords=None,            # None = lista por defecto
    reject_if_male=True,             # rechazar género masculino declarado
    reject_profile_emojis=True,      # rechazar emojis trans / pride
    reject_nonbinary_pronouns=True,  # rechazar they/them, ze/zir, etc.
    save_liked_photos=False,         # guardar primera foto de likes
    liked_photos_dir="data/liked",   # directorio de fotos
    browse_photos=3,                 # fotos a pasar al abrir el perfil
    browse_photos_delay=0.10,        # segundos entre fotos
    browse_before_like=1,            # abrir y cerrar perfil antes de swipe
)
```

### `Session.get_geomatch()`

```python
geomatch = session.get_geomatch(quickload=True, browse_photos=1)
print(geomatch.get_name(), geomatch.get_age(), geomatch.get_bio())
print(geomatch.get_genders())       # lista de géneros declarados
print(geomatch.get_passions())      # lista de intereses
print(geomatch.get_image_urls())    # URLs de fotos
```

### `Session.navigate_to()`

```python
# Dar likes en secciones distintas de la app
session.navigate_to("recs")           # recomendaciones (por defecto)
session.navigate_to("explore")        # explorar
session.navigate_to("explore/events") # eventos
session.like(amount=20)
```

### Otras acciones

```python
session.dislike(amount=5)
session.superlike(amount=1)
session.set_custom_location(latitude=40.4168, longitude=-3.7038)  # Madrid
session.set_distance_range(km=30)
session.set_age_range(18, 35)

# Matches y mensajes
matches = session.get_new_matches(amount=20)
for m in matches:
    session.send_message(m.get_chat_id(), "Hola {}!".format(m.get_name()))
    session.send_gif(m.get_chat_id(), "hello")
    session.store_local(m)  # guardar datos en data/matches/

# Guardar geomatch localmente (JSON + imágenes)
session.store_local(geomatch)
```

---

## Cómo evitar el baneo

### 1. Perfiles nuevos: mucho cuidado

Los perfiles recién creados son mucho más susceptibles al baneo. Sé especialmente cauto los primeros días.

### 2. No uses URLs

Ni en mensajes ni en la bio. Es una de las señales más fuertes de spam.

### 3. No lo dejes correr de noche sin supervisión

Si aparece un CAPTCHA mientras duermes, la sesión quedará bloqueada. Supervisa la ejecución.

### 4. Pausa entre swipes

Configura `sleep` con un valor realista. Se recomienda:
- Perfil nuevo: `sleep=3` o más.
- Perfil con antigüedad: `sleep=1.5` mínimo.
- `randomize_sleep=True` (activado por defecto) añade variación natural.

### 5. Alterna likes y dislikes

Usar `ratio` menor al 100% simula comportamiento humano. `97.5%` es un buen equilibrio.

### 6. Configura bien el perfil

- Verifica tu perfil con el badge azul.
- Vincula Instagram, Spotify o Facebook.
- Escribe una bio de al menos 100 caracteres.
- Sube mínimo 3-4 fotos de calidad.

---

## Análisis de datos

Al hacer scraping con `store_local()`, los perfiles se guardan en JSON bajo `data/`:

```
data/
├── geomatches/
│   ├── geomatches.json
│   └── images/
└── matches/
    ├── matches.json
    └── images/
```

Con esos datos puedes hacer análisis como:
- **Wordclouds** de las bios más comunes o los nombres más frecuentes.
- **Estadísticas** de edad media, número de fotos por perfil, palabras más usadas.
- **Perfil promedio**: calcular cómo es el perfil estadísticamente medio de tu zona.

---

## Aviso legal

Usar software automatizado en Tinder o Bumble va en contra de sus términos de servicio y puede resultar en el baneo permanente de la cuenta.

El scraping de perfiles no solo va contra las políticas de ambas plataformas, sino que en muchos países es ilegal. Las personas en estas apps no dieron su consentimiento para ser almacenadas por terceros y tienen derecho al olvido (ver: [RGPD en Europa](https://ec.europa.eu/info/law/law-topic/data-protection/data-protection-eu_en)).

**Este software es únicamente para fines educativos.** No se hace responsable de ninguna consecuencia derivada de su uso: ni personal (cuenta baneada) ni legal (demandas por violación de privacidad).
