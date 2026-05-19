"""
Filtros de perfil compartidos (Tinder, Bumble): palabras clave, emojis y pronombres.
"""
import re
import unicodedata
from typing import Any, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Género declarado en la app (reject_if_male)
# ---------------------------------------------------------------------------
MALE_GENDER_KEYWORDS = frozenset({
    "man", "men", "hombre", "male", "chico", "homme", "homem", "hommes", "uomo",
    "männlich", "masculino", "macho", "boy", "boys",
})
FEMALE_GENDER_KEYWORDS = frozenset({
    "woman", "women", "mujer", "female", "chica", "chicas", "femme", "femmes",
    "mulher", "donna", "weiblich", "femenino", "girl", "girls",
})

# ---------------------------------------------------------------------------
# Palabras clave por defecto: trans / no-binario / LGBTQ+
# ---------------------------------------------------------------------------
DEFAULT_REJECT_KEYWORDS_TRANS_GAY = [
    # Trans / crossdressing
    "transgender",
    "transsexual",
    "transexual",
    "trans woman",
    "trans man",
    "transwoman",
    "transman",
    "trans girl",
    "trans guy",
    "crossdresser",
    "cross-dresser",
    "crossdressing",
    "crossdress",
    "cross-dress",
    "crossdresses",
    "cross-dresses",
    "cross dresses",
    "cross dress",
    "cross dresser",
    "cross dressers",
    "xdress",
    "xdresser",
    "xdressing",
    "cd",
    "c/d",
    "travesti",
    "travestis",
    "travestismo",
    "travestida",
    "travestido",
    "travestidas",
    "travestidos",
    "transvestite",
    "transvestites",
    "transvestism",
    "transvesti",
    "tv/ts",
    "tv ts",
    "t-girl",
    "t girl",
    "tgirl",
    "m2f",
    "f2m",
    "en femme",
    "femboy",
    # No-binario / género no conforme
    "non-binary",
    "nonbinary",
    "non binary",
    "genderfluid",
    "gender fluid",
    "genderqueer",
    "gender queer",
    "transfem",
    "transfeminine",
    "transmasc",
    "transmasculine",
    "mtf",
    "ftm",
    "enby",
    "agender",
    "genderless",
    "neutrois",
    "bigender",
    "pangender",
    "genderflux",
    "demiboy",
    "demi-boy",
    "demigirl",
    "demi-girl",
    "gender non-conforming",
    "gnc",
    "androgyne",
    "two spirit",
    "two-spirit",
    "twospirit",
    "questioning",
    "intersex",
    # Médico / transición
    "hormone replacement",
    "hormone therapy",
    "terapia hormonal",
    "pre-op",
    "post-op",
    "pre op",
    "post op",
    "amab",
    "afab",
    # Drag
    "drag queen",
    "drag king",
    "drag performer",
    "drag artist",
    # Gay / lésbica / LGBTQ+
    "homosexual",
    "homosexuales",
    "lesbian",
    "lesbiana",
    "lesbianas",
    "pansexual",
    "pan sexual",
    "asexual",
    "demisexual",
    "aromantic",
    "sapphic",
    "wlw",
    "butch",
    "stud",
    "lgbt",
    "lgbtq",
    "lgbtqia",
    "lgbt+",
    "lgbtq+",
    "lgbtqia+",
    "queer",
    "orgullo gay",
    "gay pride",
    "nblm",
    "nblw",
    # Alemán
    "schwul",
    "lesbisch",
    "bisexuell",
    "transgeschlechtlich",
    "transsexuell",
    # Francés
    "lesbienne",
    "bisexuel",
    "bisexuelle",
    "transgenre",
    "transsexuel",
    # Italiano
    "lesbica",
    "bisessuale",
    "transessuale",
    # Portugués
    "lésbica",
    "lésbicas",
    "bissexual",
    # Cortos con word-boundary (ver keyword_matches_in_lower_text)
    "gay",
    "gays",
    "trans",
]

# ---------------------------------------------------------------------------
# Secuencias emoji (NFC / NFD)
# 🏳️‍⚧️ trans flag, ⚧️ trans symbol, 🏳️‍🌈 pride flag
# 🌈 rainbow, ⚢ lesbian, ⚣ gay, ⚥ intersex/bisexual
# ---------------------------------------------------------------------------
REJECT_PROFILE_EMOJI_SEQUENCES = (
    # Trans flag 🏳️‍⚧️ y variantes (con/sin selector FE0F)
    "\U0001F3F3️‍⚧️",
    "\U0001F3F3‍⚧️",
    "\U0001F3F3️‍⚧",
    "\U0001F3F3‍⚧",
    # Trans symbol ⚧️ y variante sin selector
    "⚧️",
    "⚧",
    # Pride flag 🏳️‍🌈 y variante
    "\U0001F3F3️‍\U0001F308",
    "\U0001F3F3‍\U0001F308",
    # Rainbow 🌈 (uso autónomo frecuente en perfiles LGBTQ+)
    "\U0001F308",
    # ⚢ símbolo lésbica  (U+26A2)
    "⚢",
    # ⚣ símbolo gay       (U+26A3)
    "⚣",
    # ⚥ intersex/bisexual (U+26A5)
    "⚥",
)

# ---------------------------------------------------------------------------
# Detección de pronombres no-binarios / trans
# ---------------------------------------------------------------------------
# they/them, ze/zir, xe/xem, fae/faer, ey/em, ve/ver, ne/nem, per/pers
_PRONOUN_NONBINARY = re.compile(
    r"\b(they|ze|xe|fae|ey|ve|ne|per)"
    r"[/\s]+"
    r"(them|zir|xem|faer|em|eim|ver|nem|pers)\b",
    re.IGNORECASE,
)
# Pronombres mixtos he+she en cualquier orden → perfil trans
_PRONOUN_MIXED = re.compile(
    r"\b(she|her)[/\s]+(he|him)\b|\b(he|him)[/\s]+(she|her)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Funciones públicas
# ---------------------------------------------------------------------------

def text_contains_reject_profile_emoji(text: Optional[str]) -> bool:
    if not text:
        return False
    for normalized in (
        unicodedata.normalize("NFC", text),
        unicodedata.normalize("NFD", text),
    ):
        for seq in REJECT_PROFILE_EMOJI_SEQUENCES:
            if seq in normalized:
                return True
    return False


def text_contains_nonbinary_pronouns(text: Optional[str]) -> bool:
    """Detecta they/them, ze/zir, xe/xem, fae/faer y combinaciones he+she."""
    if not text:
        return False
    return bool(_PRONOUN_NONBINARY.search(text) or _PRONOUN_MIXED.search(text))


def keyword_matches_in_lower_text(text_lower: str, keyword: str) -> bool:
    """Frases multi-palabra: subcadena; una palabra ≤4 chars: límite de palabra para reducir falsos positivos."""
    if not text_lower or not keyword:
        return False
    k = keyword.lower().strip()
    if not k:
        return False
    if " " in k:
        return k in text_lower
    if len(k) <= 5:
        return bool(re.search(r"(?<!\w)" + re.escape(k) + r"(?!\w)", text_lower))
    return k in text_lower


def build_profile_filter_texts(profile: Any) -> Tuple[str, str]:
    """(texto_minúsculas, texto_original) para palabras clave, emojis y pronombres.
    Incluye: nombre, bio, busco, trabajo, estudios, ciudad, instagram, himno, pasiones, lifestyle, basics, géneros."""
    parts: List[str] = []
    for getter in (
        "get_name", "get_bio", "get_looking_for",
        "get_work", "get_study", "get_home", "get_instagram",
    ):
        fn = getattr(profile, getter, None)
        if callable(fn):
            v = fn()
            if v:
                parts.append(str(v))
    afn = getattr(profile, "get_anthem", None)
    if callable(afn):
        av = afn()
        if isinstance(av, dict):
            parts.extend(str(x) for x in av.values() if x)
        elif av:
            parts.append(str(av))
    for getter in ("get_passions", "get_lifestyle", "get_basics"):
        fn = getattr(profile, getter, None)
        if callable(fn):
            v = fn()
            if isinstance(v, list):
                parts.extend(str(x) for x in v if x)
            elif v:
                parts.append(str(v))
    # Géneros declarados en la app (ej. "Trans Woman", "Non-binary", "Genderqueer")
    gfn = getattr(profile, "get_genders", None)
    if callable(gfn):
        gv = gfn()
        if isinstance(gv, list):
            parts.extend(str(x) for x in gv if x)
        elif gv:
            parts.append(str(gv))
    raw = " ".join(parts)
    return raw.lower(), raw


def is_male_gender_string(gender_str: Optional[str]) -> bool:
    if not gender_str:
        return False
    g = (gender_str or "").lower().strip()
    for kw in FEMALE_GENDER_KEYWORDS:
        if kw in g or g in kw:
            return False
    words = g.split()
    for w in words:
        if w in FEMALE_GENDER_KEYWORDS:
            return False
    if g in MALE_GENDER_KEYWORDS:
        return True
    for w in words:
        if w in MALE_GENDER_KEYWORDS:
            return True
    if "man" in g and "woman" not in g and "women" not in g:
        return True
    if "hombre" in g or "male" in g or "chico" in g or "homme" in g or "homem" in g:
        return True
    return False


def should_reject_profile(
    profile: Any,
    reject_keywords: Optional[List[str]],
    reject_if_male: bool,
    reject_profile_emojis: bool = True,
    reject_nonbinary_pronouns: bool = True,
) -> Tuple[bool, str]:
    """
    Devuelve (rechazar: bool, motivo: str).

    Escanea: nombre, bio, busco, trabajo, estudios, ciudad, instagram,
             himno, pasiones, lifestyle, basics.

    Parámetros
    ----------
    reject_keywords          : lista de términos; None → no se aplica aquí.
    reject_if_male           : rechazar si el género declarado es masculino.
    reject_profile_emojis    : detectar 🏳️‍⚧️ ⚧️ 🏳️‍🌈 🌈 ⚢ ⚣ ⚥.
    reject_nonbinary_pronouns: detectar they/them, ze/zir, xe/xem, fae/faer,
                               pronombres mixtos he+she.
    """
    text_lower, text_raw = build_profile_filter_texts(profile)

    if reject_profile_emojis and text_contains_reject_profile_emoji(text_raw):
        return True, "Emoji (trans / pride)"

    if reject_nonbinary_pronouns and text_contains_nonbinary_pronouns(text_raw):
        return True, "Pronombres no-binarios / trans"

    if reject_keywords:
        for kw in reject_keywords:
            if not kw or not str(kw).strip():
                continue
            if keyword_matches_in_lower_text(text_lower, str(kw)):
                return True, "Palabra clave '{}'".format(str(kw).strip())

    if not reject_if_male:
        return False, ""
    gfn = getattr(profile, "get_genders", None)
    if not callable(gfn):
        return False, ""
    genders = gfn()
    if not genders:
        return False, ""
    if len(genders) == 2:
        if is_male_gender_string(genders[0]):
            return True, "Género Hombre"
        if is_male_gender_string(genders[1]):
            return True, "Género Hombre"
        return False, ""
    if is_male_gender_string(genders[0]):
        return True, "Género Hombre"
    return False, ""
