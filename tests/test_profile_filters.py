"""
Tests unitarios para core/profile_filters.py

Cubre:
  - keyword_matches_in_lower_text: word-boundary, substring, multi-palabra, falsos positivos
  - text_contains_reject_profile_emoji: trans flag, pride flag, símbolos
  - text_contains_nonbinary_pronouns: they/them, ze/zir, pronombres mixtos he+she
  - is_male_gender_string: masculino, femenino, trans, edge cases
  - build_profile_filter_texts: campos incluidos, géneros, vacíos
  - should_reject_profile: flujo completo, filtros desactivados, falsos positivos
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from core.profile_filters import (
    DEFAULT_REJECT_KEYWORDS_TRANS_GAY,
    build_profile_filter_texts,
    is_male_gender_string,
    keyword_matches_in_lower_text,
    should_reject_profile,
    text_contains_nonbinary_pronouns,
    text_contains_reject_profile_emoji,
)


# ---------------------------------------------------------------------------
# MockProfile: simula un perfil sin browser ni red
# ---------------------------------------------------------------------------

class MockProfile:
    def __init__(
        self,
        name=None, bio=None, looking_for=None, work=None, study=None,
        home=None, instagram=None, anthem=None, passions=None,
        lifestyle=None, basics=None, genders=None,
    ):
        self._name = name
        self._bio = bio
        self._looking_for = looking_for
        self._work = work
        self._study = study
        self._home = home
        self._instagram = instagram
        self._anthem = anthem
        self._passions = passions or []
        self._lifestyle = lifestyle or []
        self._basics = basics or []
        self._genders = genders or []

    def get_name(self): return self._name
    def get_bio(self): return self._bio
    def get_looking_for(self): return self._looking_for
    def get_work(self): return self._work
    def get_study(self): return self._study
    def get_home(self): return self._home
    def get_instagram(self): return self._instagram
    def get_anthem(self): return self._anthem
    def get_passions(self): return self._passions
    def get_lifestyle(self): return self._lifestyle
    def get_basics(self): return self._basics
    def get_genders(self): return self._genders


# ===========================================================================
# keyword_matches_in_lower_text
# ===========================================================================

class TestKeywordMatching:

    # ---- "trans": word-boundary (5 chars) ----

    def test_trans_not_in_transport(self):
        assert not keyword_matches_in_lower_text("i use public transport daily", "trans")

    def test_trans_not_in_tranquil(self):
        assert not keyword_matches_in_lower_text("feeling very tranquil today", "trans")

    def test_trans_not_in_translate(self):
        assert not keyword_matches_in_lower_text("i translate novels", "trans")

    def test_trans_not_in_transfer(self):
        assert not keyword_matches_in_lower_text("bank transfer confirmed", "trans")

    def test_trans_matches_standalone(self):
        assert keyword_matches_in_lower_text("i'm trans", "trans")

    def test_trans_matches_start_of_sentence(self):
        assert keyword_matches_in_lower_text("trans woman looking for love", "trans")

    def test_trans_matches_at_end(self):
        assert keyword_matches_in_lower_text("proud and trans", "trans")

    def test_trans_matches_with_punctuation(self):
        assert keyword_matches_in_lower_text("i am trans, 25, madrid", "trans")

    # ---- "transgender" / "transgenero": substring (> 5 chars) ----

    def test_transgender_in_bio(self):
        assert keyword_matches_in_lower_text("i am transgender", "transgender")

    def test_transgender_in_compound(self):
        assert keyword_matches_in_lower_text("all transgenders welcome", "transgender")

    def test_transgenero_spanish_uppercase(self):
        assert keyword_matches_in_lower_text("transgenero", "transgenero")

    def test_transgenero_spanish_accent(self):
        assert keyword_matches_in_lower_text("soy transgénero", "transgénero")

    def test_transgenero_uppercase_bio(self):
        assert keyword_matches_in_lower_text("TRANSGENERO".lower(), "transgenero")

    # ---- "butch": word-boundary (5 chars) ----

    def test_butch_not_in_butcher(self):
        assert not keyword_matches_in_lower_text("my dad is a butcher", "butch")

    def test_butch_matches_standalone(self):
        assert keyword_matches_in_lower_text("butch lesbian vibes", "butch")

    # ---- "gay": word-boundary (3 chars) ----

    def test_gay_matches_standalone(self):
        assert keyword_matches_in_lower_text("soy gay y orgullosa", "gay")

    def test_gay_not_in_compound(self):
        # "gaylord" es un nombre de ciudad — "gay" seguido de "l" (word char) → no match
        assert not keyword_matches_in_lower_text("i'm from gaylord, michigan", "gay")

    def test_gay_not_in_gaymer(self):
        assert not keyword_matches_in_lower_text("proud gaymer here", "gay")

    # ---- frases multi-palabra ----

    def test_multiword_drag_queen(self):
        assert keyword_matches_in_lower_text("i do drag queen shows", "drag queen")

    def test_multiword_partial_no_match(self):
        assert not keyword_matches_in_lower_text("i do drag", "drag queen")

    def test_multiword_non_binary(self):
        assert keyword_matches_in_lower_text("i am non-binary", "non-binary")

    def test_multiword_trans_woman(self):
        assert keyword_matches_in_lower_text("proud trans woman", "trans woman")

    # ---- "lesbian": substring (6 chars) ----

    def test_lesbian_matches(self):
        assert keyword_matches_in_lower_text("i am a lesbian", "lesbian")

    def test_lesbian_matches_in_lesbiana(self):
        # "lesbiana" (español) contiene "lesbian" como subcadena → captura
        assert keyword_matches_in_lower_text("soy lesbiana", "lesbian")

    # ---- edge cases ----

    def test_empty_text(self):
        assert not keyword_matches_in_lower_text("", "trans")

    def test_empty_keyword(self):
        assert not keyword_matches_in_lower_text("some text", "")

    def test_none_text(self):
        assert not keyword_matches_in_lower_text(None, "trans")

    def test_case_insensitive_text(self):
        # La función espera texto ya en minúsculas; si viene en mayúsculas no debe dar falso positivo
        # (en la práctica build_profile_filter_texts normaliza a lower)
        assert keyword_matches_in_lower_text("proud trans person", "trans")


# ===========================================================================
# text_contains_reject_profile_emoji
# ===========================================================================

class TestEmojiDetection:

    def test_trans_symbol(self):
        assert text_contains_reject_profile_emoji("hello ⚧ world")

    def test_trans_symbol_with_variation_selector(self):
        assert text_contains_reject_profile_emoji("⚧️ proud")

    def test_pride_flag(self):
        assert text_contains_reject_profile_emoji("🏳️‍🌈 living my best life")

    def test_rainbow_standalone(self):
        assert text_contains_reject_profile_emoji("I love 🌈")

    def test_lesbian_symbol(self):
        assert text_contains_reject_profile_emoji("⚢")

    def test_gay_symbol(self):
        assert text_contains_reject_profile_emoji("⚣")

    def test_intersex_symbol(self):
        assert text_contains_reject_profile_emoji("⚥")

    def test_normal_food_emoji_no_match(self):
        assert not text_contains_reject_profile_emoji("love pizza 🍕 and 🍝")

    def test_heart_emoji_no_match(self):
        assert not text_contains_reject_profile_emoji("looking for love ❤️")

    def test_sun_emoji_no_match(self):
        assert not text_contains_reject_profile_emoji("good vibes ☀️")

    def test_empty_string(self):
        assert not text_contains_reject_profile_emoji("")

    def test_none_value(self):
        assert not text_contains_reject_profile_emoji(None)

    def test_plain_text_no_match(self):
        assert not text_contains_reject_profile_emoji("hola, soy María, me gusta viajar")


# ===========================================================================
# text_contains_nonbinary_pronouns
# ===========================================================================

class TestPronounDetection:

    # ---- pronombres no-binarios estándar ----

    def test_they_them_slash(self):
        assert text_contains_nonbinary_pronouns("pronouns: they/them")

    def test_they_them_space(self):
        assert text_contains_nonbinary_pronouns("they them")

    def test_ze_zir(self):
        assert text_contains_nonbinary_pronouns("ze/zir")

    def test_xe_xem(self):
        assert text_contains_nonbinary_pronouns("xe/xem")

    def test_fae_faer(self):
        assert text_contains_nonbinary_pronouns("fae/faer")

    def test_ey_em(self):
        assert text_contains_nonbinary_pronouns("ey/em")

    def test_ve_ver(self):
        assert text_contains_nonbinary_pronouns("ve/ver")

    # ---- pronombres mixtos (indicador trans) ----

    def test_mixed_she_he(self):
        assert text_contains_nonbinary_pronouns("she/her he/him")

    def test_mixed_he_she(self):
        assert text_contains_nonbinary_pronouns("he/him she/her")

    def test_mixed_she_space_he(self):
        assert text_contains_nonbinary_pronouns("she her he him")

    # ---- pronombres normales: NO deben disparar el filtro ----

    def test_she_her_alone_no_match(self):
        assert not text_contains_nonbinary_pronouns("she/her")

    def test_he_him_alone_no_match(self):
        assert not text_contains_nonbinary_pronouns("he/him")

    def test_she_in_sentence_no_match(self):
        assert not text_contains_nonbinary_pronouns("she loves hiking")

    # ---- misc ----

    def test_case_insensitive_they(self):
        assert text_contains_nonbinary_pronouns("THEY/THEM")

    def test_empty_string(self):
        assert not text_contains_nonbinary_pronouns("")

    def test_none_value(self):
        assert not text_contains_nonbinary_pronouns(None)


# ===========================================================================
# is_male_gender_string
# ===========================================================================

class TestMaleGenderDetection:

    def test_man_is_male(self):
        assert is_male_gender_string("Man")

    def test_hombre_is_male(self):
        assert is_male_gender_string("Hombre")

    def test_male_is_male(self):
        assert is_male_gender_string("Male")

    def test_boy_is_male(self):
        assert is_male_gender_string("Boy")

    def test_woman_is_not_male(self):
        assert not is_male_gender_string("Woman")

    def test_mujer_is_not_male(self):
        assert not is_male_gender_string("Mujer")

    def test_girl_is_not_male(self):
        assert not is_male_gender_string("Girl")

    def test_trans_woman_is_not_male(self):
        # Contiene "woman" → femenino → no es "male" para reject_if_male
        assert not is_male_gender_string("Trans Woman")

    def test_nonbinary_is_not_male(self):
        assert not is_male_gender_string("Non-binary")

    def test_none_is_not_male(self):
        assert not is_male_gender_string(None)

    def test_empty_is_not_male(self):
        assert not is_male_gender_string("")

    def test_woman_not_confused_with_man(self):
        # "woman" contiene "man" → el código debe priorizar femenino
        assert not is_male_gender_string("Woman")

    def test_women_not_confused_with_men(self):
        assert not is_male_gender_string("Women")


# ===========================================================================
# build_profile_filter_texts
# ===========================================================================

class TestBuildFilterTexts:

    def test_gender_included(self):
        p = MockProfile(genders=["Trans Woman"])
        lower, raw = build_profile_filter_texts(p)
        assert "trans woman" in lower

    def test_multiple_genders_included(self):
        p = MockProfile(genders=["Non-binary", "Genderqueer"])
        lower, _ = build_profile_filter_texts(p)
        assert "non-binary" in lower
        assert "genderqueer" in lower

    def test_bio_included(self):
        p = MockProfile(bio="I love hiking and coffee")
        lower, _ = build_profile_filter_texts(p)
        assert "hiking" in lower

    def test_passions_included(self):
        p = MockProfile(passions=["LGBTQ+ Rights", "Travel"])
        lower, _ = build_profile_filter_texts(p)
        assert "lgbtq+" in lower

    def test_work_included(self):
        p = MockProfile(work="Software Engineer at Acme")
        lower, _ = build_profile_filter_texts(p)
        assert "software engineer" in lower

    def test_looking_for_included(self):
        p = MockProfile(looking_for="queer community")
        lower, _ = build_profile_filter_texts(p)
        assert "queer community" in lower

    def test_basics_included(self):
        p = MockProfile(basics=["Non-binary"])
        lower, _ = build_profile_filter_texts(p)
        assert "non-binary" in lower

    def test_anthem_dict_included(self):
        p = MockProfile(anthem={"song": "Born This Way", "artist": "Lady Gaga"})
        lower, _ = build_profile_filter_texts(p)
        assert "born this way" in lower
        assert "lady gaga" in lower

    def test_empty_profile_returns_empty(self):
        p = MockProfile()
        lower, raw = build_profile_filter_texts(p)
        assert lower == ""
        assert raw == ""

    def test_raw_preserves_case(self):
        p = MockProfile(name="María")
        lower, raw = build_profile_filter_texts(p)
        assert "maría" in lower
        assert "María" in raw

    def test_genders_empty_list_no_crash(self):
        p = MockProfile(genders=[])
        lower, raw = build_profile_filter_texts(p)
        assert isinstance(lower, str)


# ===========================================================================
# should_reject_profile (flujo completo)
# ===========================================================================

class TestShouldRejectProfile:
    KW = list(DEFAULT_REJECT_KEYWORDS_TRANS_GAY)

    def _reject(self, profile, **kw):
        return should_reject_profile(
            profile,
            reject_keywords=kw.get("reject_keywords", self.KW),
            reject_if_male=kw.get("reject_if_male", True),
            reject_profile_emojis=kw.get("reject_profile_emojis", True),
            reject_nonbinary_pronouns=kw.get("reject_nonbinary_pronouns", True),
        )

    # ---- trans en bio → rechazado ----

    def test_trans_in_bio_rejected(self):
        p = MockProfile(bio="I'm trans and proud")
        rejected, reason = self._reject(p)
        assert rejected

    def test_transgender_in_bio_rejected(self):
        p = MockProfile(bio="I am transgender")
        rejected, _ = self._reject(p)
        assert rejected

    def test_transsexual_in_bio_rejected(self):
        p = MockProfile(bio="transexual woman")
        rejected, _ = self._reject(p)
        assert rejected

    # ---- trans en el campo género → rechazado (bug corregido) ----

    def test_trans_woman_gender_rejected(self):
        p = MockProfile(genders=["Trans Woman"])
        rejected, reason = self._reject(p)
        assert rejected, "Una persona con género 'Trans Woman' debe ser rechazada"

    def test_nonbinary_gender_rejected(self):
        p = MockProfile(genders=["Non-binary"])
        rejected, _ = self._reject(p)
        assert rejected

    def test_genderqueer_gender_rejected(self):
        p = MockProfile(genders=["Genderqueer"])
        rejected, _ = self._reject(p)
        assert rejected

    def test_genderfluid_in_bio_rejected(self):
        p = MockProfile(bio="genderfluid and proud")
        rejected, _ = self._reject(p)
        assert rejected

    # ---- "transport" NO dispara el filtro (falso positivo corregido) ----

    def test_transport_in_bio_not_rejected(self):
        p = MockProfile(bio="Trabajo en el sector del transporte público", genders=["Woman"])
        rejected, _ = self._reject(p)
        assert not rejected, "Transport no debe activar el filtro 'trans'"

    def test_translate_in_bio_not_rejected(self):
        p = MockProfile(bio="I translate books from English to Spanish", genders=["Woman"])
        rejected, _ = self._reject(p)
        assert not rejected

    def test_transfer_in_bio_not_rejected(self):
        p = MockProfile(bio="I do bank transfers for a living", genders=["Woman"])
        rejected, _ = self._reject(p)
        assert not rejected

    # ---- perfil femenino normal → pasa ----

    def test_normal_woman_passes(self):
        p = MockProfile(bio="Love hiking, good coffee and sunsets", genders=["Woman"])
        rejected, _ = self._reject(p)
        assert not rejected

    def test_normal_woman_no_bio_passes(self):
        p = MockProfile(genders=["Woman"])
        rejected, _ = self._reject(p)
        assert not rejected

    def test_normal_woman_no_gender_no_bio_passes(self):
        # Sin datos, no hay nada que rechazar
        p = MockProfile(name="Ana")
        rejected, _ = self._reject(p)
        assert not rejected

    # ---- hombre → rechazado (reject_if_male) ----

    def test_male_gender_rejected(self):
        p = MockProfile(genders=["Man"])
        rejected, reason = self._reject(p)
        assert rejected
        assert "hombre" in reason.lower() or "género" in reason.lower()

    def test_hombre_gender_rejected(self):
        p = MockProfile(genders=["Hombre"])
        rejected, _ = self._reject(p)
        assert rejected

    # ---- emojis ----

    def test_pride_flag_in_bio_rejected(self):
        p = MockProfile(bio="🏳️‍🌈 living my best life")
        rejected, reason = self._reject(p)
        assert rejected
        assert "emoji" in reason.lower()

    def test_trans_emoji_rejected(self):
        p = MockProfile(bio="⚧️ proud")
        rejected, _ = self._reject(p)
        assert rejected

    def test_rainbow_in_bio_rejected(self):
        p = MockProfile(bio="love and 🌈 everywhere")
        rejected, _ = self._reject(p)
        assert rejected

    # ---- pronombres ----

    def test_they_them_pronouns_rejected(self):
        p = MockProfile(bio="they/them pronouns please")
        rejected, reason = self._reject(p)
        assert rejected
        assert "pronombre" in reason.lower()

    def test_mixed_pronouns_rejected(self):
        p = MockProfile(bio="she/her he/him")
        rejected, _ = self._reject(p)
        assert rejected

    def test_normal_she_her_not_rejected_by_pronouns(self):
        # she/her solamente no activa el filtro de pronombres
        p = MockProfile(bio="she/her, I love dogs and hiking", genders=["Woman"])
        rejected, _ = self._reject(p)
        assert not rejected

    # ---- keywords en otros campos ----

    def test_lgbt_in_passions_rejected(self):
        p = MockProfile(passions=["LGBTQ+ Rights", "Travel"])
        rejected, _ = self._reject(p)
        assert rejected

    def test_queer_in_looking_for_rejected(self):
        p = MockProfile(looking_for="queer community")
        rejected, _ = self._reject(p)
        assert rejected

    def test_gay_in_work_rejected(self):
        p = MockProfile(work="Gay bar manager")
        rejected, _ = self._reject(p)
        assert rejected

    # ---- filtros desactivados individualmente ----

    def test_emoji_filter_disabled_passes(self):
        # Solo emoji (sin texto keyword) → pasa si emoji desactivado
        p = MockProfile(bio="🏳️‍🌈 living my best life", genders=["Woman"])
        rejected, _ = self._reject(p, reject_profile_emojis=False, reject_keywords=[])
        # La bio no tiene keywords de texto ni género masculino → pasa
        assert not rejected

    def test_pronoun_filter_disabled_passes(self):
        # "they/them" sin keywords de texto → pasa si pronombres desactivados
        p = MockProfile(bio="they/them pronouns please", genders=["Woman"])
        rejected, _ = self._reject(p, reject_nonbinary_pronouns=False, reject_keywords=[])
        assert not rejected

    def test_male_filter_disabled_passes(self):
        p = MockProfile(genders=["Man"])
        rejected, _ = self._reject(p, reject_if_male=False, reject_keywords=[])
        assert not rejected

    def test_all_filters_disabled_passes(self):
        p = MockProfile(bio="I am transgender gay lesbian", genders=["Trans Woman"])
        rejected, _ = should_reject_profile(
            p,
            reject_keywords=[],
            reject_if_male=False,
            reject_profile_emojis=False,
            reject_nonbinary_pronouns=False,
        )
        assert not rejected

    # ---- motivo devuelto ----

    def test_reason_keyword(self):
        p = MockProfile(bio="I am transgender")
        rejected, reason = self._reject(p)
        assert rejected
        assert "palabra clave" in reason.lower() or "transgender" in reason.lower()

    def test_reason_emoji(self):
        p = MockProfile(bio="⚧️")
        rejected, reason = self._reject(p)
        assert rejected
        assert "emoji" in reason.lower()

    def test_reason_pronouns(self):
        p = MockProfile(bio="they/them")
        rejected, reason = self._reject(p)
        assert rejected
        assert "pronombre" in reason.lower()

    def test_reason_gender_male(self):
        p = MockProfile(genders=["Man"])
        rejected, reason = self._reject(p)
        assert rejected
        assert "hombre" in reason.lower() or "género" in reason.lower()

    def test_not_rejected_returns_empty_reason(self):
        p = MockProfile(genders=["Woman"])
        rejected, reason = self._reject(p)
        assert not rejected
        assert reason == ""
