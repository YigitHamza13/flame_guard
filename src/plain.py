"""Plain-language cargo cards: free-text cargo → closest NASA specimen, one-sentence summary, colour tone.

Colour is a reading aid only, never a safety rating. Every card also says it in words.
"""
import html

from src.links import platform as _platform

import streamlit as st

from src.i18n import t

# Everyday words → the NASA reference specimen they are closest to (never "the same material").
KEYWORDS = {
    "pamuklu kumaş": ["cotton", "pamuk", "fabric", "kumaş", "textile", "tekstil", "towel", "havlu", "clothing", "giysi",
                      "kıyafet", "sibal", "curtain", "perde"],
    "kablo kılıfı": ["cable", "kablo", "wire", "tel", "insulation", "yalıtım", "cord"],
    "kauçuk": ["rubber", "kauçuk", "silicone", "silikon", "elastomer", "gasket", "conta", "seal"],
    "kağıt": ["paper", "kağıt", "kâğıt", "cellulose", "selüloz", "notebook", "defter", "napkin", "peçete", "tissue"],
}

# Extra NASA specimens from a separate verified table (data/additional_specimens.json); checked first.
EXTRA_KEYWORDS = {
    "jersey_extra": ["t-shirt", "tshirt", "tişört", "tisort", "jersey", "shirt", "gömlek"],
    "pmma_extra": ["acrylic", "akrilik", "pmma", "plexiglass", "pleksi", "plexi", "window", "pencere"],
    "hdpe_extra": ["bottle", "şişe", "container", "hdpe", "plastic box", "plastik kutu", "plastik kap", "food box", "saklama kabı"],
    "delrin_extra": ["delrin", "acetal", "asetal", "gear", "dişli", "knob", "düğme"],
    "nomex_extra": ["nomex", "flight suit", "uçuş tulumu", "tulum", "coverall"],
}

SUGGESTIONS = [("Cotton T-shirt", "Pamuklu tişört"), ("Bath towel", "Banyo havlusu"), ("Headphone cable", "Kulaklık kablosu"),
               ("Silicone gasket", "Silikon conta"), ("Notebook", "Defter"), ("Acrylic window", "Akrilik pencere"),
               ("Plastic water bottle (HDPE)", "Plastik su şişesi (HDPE)"), ("Delrin gear", "Delrin dişli"),
               ("Nomex flight suit", "Nomex uçuş tulumu"), ("Laptop", "Dizüstü bilgisayar")]


def suggestions() -> list:
    return [tr if _tr() else en for en, tr in SUGGESTIONS]


def extras() -> dict:
    import json as _json
    from src.evidence import ROOT
    data = _json.loads((ROOT / "data" / "additional_specimens.json").read_text(encoding="utf-8"))
    return {s["key"]: s for s in data["specimens"]}


def extra_name(key: str) -> str:
    s = extras()[key]
    return s["name_tr"] if _tr() else s["name_en"]

DEFAULT_ASSUMPTIONS = {
    "ISS": {"oxygen": 21.0, "pressure": 101.325, "default": True,
            "note_en": "default: about 21% O₂ and 1 atm, the cabin air of the WIF tests",
            "note_tr": "varsayılan: WIF testlerindeki kabin havası gibi yaklaşık %21 O₂ ve 1 atm"},
    "Moon Base": {"oxygen": 34.0, "pressure": 56.5, "default": True,
                  "note_en": "default: NASA's planned FM² test atmosphere, 34% O₂ at 8.2 psia (poster 20240015307, p. 1)",
                  "note_tr": "varsayılan: NASA'nın planlanan FM² test atmosferi, 8,2 psia'da %34 O₂ (poster 20240015307, s. 1)"},
    "Earth Lab": {"oxygen": 21.0, "pressure": 101.325, "default": True,
                  "note_en": "default: normal air at 1 atm", "note_tr": "varsayılan: 1 atm'de normal hava"},
}


def _tr() -> bool:
    return st.session_state.get("fg_lang", "EN") == "TR"


import re as _re

# Materials named by the user that NASA did not test in this collection: never mapped to a tested specimen.
OTHER_MATERIALS = ["glass", "cam", "metal", "metallic", "metal", "steel", "çelik", "celik", "aluminium", "aluminum", "alüminyum",
                   "iron", "demir", "copper", "bakır", "polyester", "nylon", "naylon", "wool", "yün", "leather", "deri",
                   "ceramic", "seramik", "wood", "wooden", "ahşap", "tahta", "pet", "polycarbonate", "polikarbonat",
                   "polypropylene", "polipropilen", "pvc", "porcelain", "porselen", "stainless", "paslanmaz"]
# A material word decides the specimen (checked before any object word).
MATERIAL_WORDS = [
    ("pmma_extra", ["acrylic", "akrilik", "pmma", "plexiglass", "plexiglas", "pleksi", "plexi"]),
    ("hdpe_extra", ["hdpe", "high-density polyethylene", "yüksek yoğunluklu polietilen"]),
    ("delrin_extra", ["delrin", "acetal", "asetal", "pom"]),
    ("nomex_extra", ["nomex"]),
    ("kauçuk", ["silicone", "silikon", "rubber", "kauçuk", "elastomer"]),
    ("kağıt", ["paper", "kağıt", "kâğıt", "kagit", "cellulose", "selüloz"]),
    ("jersey_extra", ["jersey"]),
]
COTTON = ["cotton", "pamuk", "pamuklu"]
GARMENT = ["shirt", "t-shirt", "tshirt", "tişört", "tisort", "gömlek", "sweatshirt", "pijama", "pyjama", "pajama"]
# Object words whose usual material matches one tested specimen closely enough.
OBJECT_WORDS = [
    ("kablo kılıfı", ["cable", "kablo", "wire", "tel", "cord", "kordon", "insulation", "yalıtım"]),
    ("kağıt", ["notebook", "defter", "napkin", "peçete", "tissue", "mendil", "checklist", "manual", "kılavuz"]),
    ("pamuklu kumaş", ["towel", "havlu"]),
    ("nomex_extra", ["flight suit", "uçuş tulumu", "coverall"]),
]
# Objects that come in several materials: the user chooses; nothing is assumed.
AMBIGUOUS = [
    (["bottle", "şişe", "sise", "container", "kap", "kutu", "box", "jar", "kavanoz"], ["hdpe_extra"]),
    (GARMENT + ["clothing", "giysi", "kıyafet", "fabric", "kumaş", "textile", "tekstil", "curtain", "perde"],
     ["jersey_extra", "pamuklu kumaş", "nomex_extra"]),
    (["window", "pencere", "screen cover", "visor", "vizör"], ["pmma_extra"]),
    (["gear", "dişli", "disli", "knob", "düğme", "button", "handle", "sap"], ["delrin_extra"]),
    (["seal", "gasket", "conta", "o-ring"], ["kauçuk"]),
]
OTHER = "__other__"


def _norm(text: str) -> str:
    return text.replace("İ", "i").replace("I", "ı" if False else "I").casefold()


def _tokens(text: str) -> list:
    low = _norm(text)
    toks = _re.findall(r"[\w]+(?:-[\w]+)*", low)
    return toks + [part for tok in toks if "-" in tok for part in tok.split("-")]


def _has(text: str, tokens: list, words: list) -> bool:
    for w in words:
        if " " in w:
            if _re.search(r"(?<![\w])" + _re.escape(w), _norm(text)):
                return True
        elif any(tok == w or (len(w) >= 4 and tok.startswith(w)) for tok in tokens):
            return True
    return False


def classify(item: str, keys: list) -> tuple:
    """(status, key, options). status: 'known' | 'match' | 'ask' | 'other_material' | 'none'.
    A named material always wins; a material NASA did not test is never mapped; an object that comes in
    several materials returns the options instead of a guess."""
    if item in keys:
        return "known", item, []
    toks = _tokens(item)
    if _has(item, toks, COTTON):
        return "match", ("jersey_extra" if _has(item, toks, GARMENT) else "pamuklu kumaş"), []
    for key, words in MATERIAL_WORDS:
        if (key in keys or key in EXTRA_KEYWORDS) and _has(item, toks, words):
            return "match", key, []
    if _has(item, toks, OTHER_MATERIALS):
        return "other_material", None, []
    for key, words in OBJECT_WORDS:
        if (key in keys or key in EXTRA_KEYWORDS) and _has(item, toks, words):
            return "match", key, []
    for words, options in AMBIGUOUS:
        if _has(item, toks, words):
            return "ask", None, [k for k in options if k in keys or k in EXTRA_KEYWORDS]
    return "none", None, []


def resolve(item: str, keys: list, choice: str | None = None) -> str | None:
    """Specimen key for a cargo item, or None. For an ambiguous item only the user's choice counts."""
    status, key, options = classify(item, keys)
    if status == "ask":
        return choice if choice in options else None
    return key


def _count(rows, column, value):
    return int(rows.loc[rows[column].eq(value), "test_count"].fillna(0).sum())


def _conditions(rows) -> str:
    o2 = rows.oxygen_pct.dropna() if "oxygen_pct" in rows else []
    p = rows.pressure_kpa.dropna() if "pressure_kpa" in rows else []
    rng = lambda v, u: t("not reported") if len(v) == 0 else (f"{v.min():g} {u}" if v.min() == v.max() else f"{v.min():g}–{v.max():g} {u}")
    return t("Test conditions: O₂ {o2}, pressure {p}.", o2=rng(o2, "%"), p=rng(p, "kPa"))


def status_card(user_word: str, status: str, filtered_out: bool = False) -> tuple:
    """Cards that show no evidence on purpose: material not chosen, a material NASA did not test, or outside the filter."""
    from src.access import say_button
    if status == "ask":
        body = t("This item comes in several materials. Choose what it is made of above; FLAMEGUARD does not guess.")
        badge = t("Choose a material")
    elif status == "other_material":
        body = t("You named a material that NASA did not test in this collection (for example glass, metal or polyester). It is not matched to a different material. Missing data does not mean safe.")
        badge = t("Material not tested here")
    elif filtered_out:
        body = t("NASA tests of this specimen exist, but none was run inside the selected oxygen range. Missing data does not mean safe.")
        badge = t("Outside the oxygen filter")
    else:
        body = t("No NASA flight test in this collection matches this item. Missing data does not mean safe.")
        badge = t("No compiled test")
    nxt = "" if status == "ask" else next_html(next_needed(None, None, "ISS"))
    return (f"<div class='plain-card tone-none'>{say_button(user_word + '. ' + body)}<div class='plain-title'>{html.escape(user_word)}</div>"
            f"<span class='plain-badge'>◌ {html.escape(badge)}</span><p>{html.escape(body)}</p>{nxt}</div>"), "none"


def card(user_word: str, key, rows, env: str, specimen_name: str, extra_scope=None, filtered_out: bool = False) -> tuple:
    """HTML card with plain sentences. rows = this specimen's rows inside the active filter.
    Observed counts are given with their conditions; no general ignition probability is derived."""
    tr = _tr()
    title = html.escape(user_word)
    if key in EXTRA_KEYWORDS:
        if extra_scope is not None and key not in extra_scope:
            return status_card(user_word, "none", filtered_out=True)
        return extra_card(user_word, key, env)
    if key is None or rows.empty:
        if filtered_out:
            return status_card(user_word, "none", filtered_out=True)
        if key is None:
            body = t("No NASA flight test in this collection matches this item. Missing data does not mean safe.")
        else:
            body = t("NASA study evidence exists for this specimen, but no compiled test count. Missing data does not mean safe.")
        from src.access import say_button
        return (f"<div class='plain-card tone-none'>{say_button(user_word + '. ' + body)}<div class='plain-title'>{title}</div>"
                f"<span class='plain-badge'>◌ {html.escape(t('No compiled test'))}</span>"
                f"<p>{html.escape(body)}</p>{next_html(next_needed(key, rows, env))}</div>"), "none"
    from src.links import platform
    n = int(rows.test_count.fillna(0).sum())
    ign = _count(rows, "ignition", "observed")
    local = _count(rows, "ignition", "local_gas_flame")
    disputed = _count(rows, "ignition", "disputed")
    spread = _count(rows, "propagation", "observed")
    no_spread = _count(rows, "propagation", "not_observed")
    sentences = [t("NASA tested this specimen in space once.") if n == 1 else t("NASA tested this specimen in space {n} times.", n=n)]
    if disputed:
        sentences.append(t("The report's ignition count is disputed, so no ignition count is shown."))
        tone = "none"
    elif local == n:
        sentences.append(t("Each time only a brief local flame appeared; it did not keep burning or spread."))
        tone = "low"
    else:
        sentences.append(t("It ignited.") if n == 1 and ign == 1 else t("It ignited in {k} of them.", k=ign))
        if spread:
            sentences.append(t("The flame spread in {s}.", s=spread))
            tone = "high"
        elif no_spread:
            sentences.append(t("The flame did not spread."))
            tone = "medium"
        else:
            sentences.append(t("The report does not say whether the flame spread."))
            tone = "medium_unknown"
    if no_spread and not local == n and spread:
        sentences.append(t("In {m} the flame did not spread.", m=no_spread))
    sentences.append(_conditions(rows))
    gravity_note = ""
    if env != "ISS":
        tone = "none"
        gravity_note = (f"<span class='plain-badge warn'>{html.escape(t('These tests were in microgravity, not this environment.'))}</span>")
    tone_label = {"high": t("Flame spread observed"), "medium": t("Ignited; spread not observed"),
                  "medium_unknown": t("Ignited; spread not reported"),
                  "low": t("Brief local flame only"), "none": t("No count shown")}[tone]
    css_tone = "medium" if tone == "medium_unknown" else tone
    where = platform(rows.experiment_id.dropna().unique(), tr) if "experiment_id" in rows else ""
    from src.access import say_button
    return (f"<div class='plain-card tone-{css_tone}'>{say_button(user_word + '. ' + ' '.join(sentences))}<div class='plain-title'>{title}"
            + (f"<span class='plain-map'> → {html.escape(specimen_name)}</span>" if specimen_name != user_word else "") + "</div>"
            f"<div class='plain-sub'>{html.escape(t('Closest NASA-tested specimen, not your exact product.'))}"
            + (f" {html.escape(t('Flown on'))}: {html.escape(where)}" if where else "") + "</div>"
            f"<span class='plain-badge'>{html.escape(tone_label)}</span>{gravity_note}"
            f"<p>{html.escape(' '.join(sentences))}</p>{next_html(next_needed(key, rows, env))}</div>"), css_tone


CSS = """<style>
.plain-card{background:var(--surface,#101a29);border:1px solid var(--line,#314156);border-left:5px solid #7d8a9c;border-radius:8px;
  padding:14px 18px;margin:8px 0}
.plain-card p{margin:8px 0 0;max-width:80ch}
.plain-title{font-size:18px;font-weight:600}.plain-map{color:var(--muted,#abbace);font-weight:400;font-size:15px}
.plain-sub{color:var(--muted,#abbace);font-size:13px;margin:2px 0 6px}
.plain-badge{display:inline-block;font-size:13px;border:1px solid var(--line,#314156);border-radius:4px;padding:3px 8px;margin-right:6px}
.plain-badge.warn{border-color:#ffb487;color:#ffb487}
.plain-card.tone-high{border-left-color:#e8704a;background:linear-gradient(135deg,rgba(232,110,72,.18),var(--surface,#101a29) 70%)}
.plain-card.tone-medium{border-left-color:#e0a53b;background:linear-gradient(135deg,rgba(224,165,59,.15),var(--surface,#101a29) 70%)}
.plain-card.tone-low{border-left-color:#5296dc;background:linear-gradient(135deg,rgba(82,150,220,.15),var(--surface,#101a29) 70%)}
.plain-card.tone-none{border-left-color:#7d8a9c;border-style:dashed solid dashed solid}
.plain-next{margin-top:8px;font-size:14px;color:#ffd2a8}
</style>"""


def legend() -> str:
    return t("Card colour is a reading aid, not a safety rating: orange = flame spread observed · amber = ignited, spread not observed or not reported (the card says which) · blue = only a brief local flame or no ignition · grey = no data, disputed count or different gravity. Blue does not mean safe. Counts are what NASA observed under the listed conditions, not a general ignition probability.")


MOOD_CSS = """<style>
/* Theme shifts softly toward red-orange when the cargo list shows flame spread (a reading aid, not a safety rating). */
.stApp{transition:background 1.2s ease, box-shadow 1.2s ease}
.stApp.fg-mood-high{background:radial-gradient(1400px 700px at 70% -12%, rgba(232,96,64,.26) 0%, rgba(214,72,56,.10) 38%, #080d16 70%) fixed!important}
.stApp.fg-mood-medium{background:radial-gradient(1400px 700px at 70% -12%, rgba(232,150,64,.20) 0%, #080d16 65%) fixed!important}
.stApp.fg-mood-high [data-testid="stSidebar"]{transition:background 1.2s ease;background:linear-gradient(180deg,#2a1712 0%,#0d1623 55%)!important}
.stApp.fg-mood-high h1,.stApp.fg-mood-high h2,.stApp.fg-mood-high h3{transition:color 1.2s ease;color:#ffc2a6}
@media (prefers-reduced-motion: reduce){.stApp,.stApp [data-testid="stSidebar"]{transition:none}}
</style>"""


def page_mood(tones: list) -> None:
    """Set a soft page tint from the strongest tone in the list; clears it otherwise."""
    order = {"high": 2, "medium": 1}
    present = [x for x in tones if x in order]
    mood = max(present, key=order.get) if present else ""
    js = ("const a=window.parent.document.querySelector('.stApp');"
          "if(a){a.classList.remove('fg-mood-high','fg-mood-medium');" + (f"a.classList.add('fg-mood-{mood}');" if mood else "") + "}")
    st.markdown(MOOD_CSS, unsafe_allow_html=True)
    st.html(f"<script>try{{{js}}}catch(e){{}}</script>", unsafe_allow_javascript=True)


def _fmt_range(r, unit):
    if not r:
        return t("not reported")
    lo, hi = r
    return f"{lo:g} {unit}" if lo == hi else f"{lo:g}–{hi:g} {unit}"


def extra_card(user_word: str, key: str, env: str) -> tuple:
    s = extras()[key]
    nm = extra_name(key)
    n, k, no = s["tests"], s["ignited"], s["not_ignited"]
    sentences = [t("NASA tested this specimen in space once.") if n == 1 else t("NASA tested this specimen in space {n} times.", n=n)]
    if k == n:
        sentences.append(t("It ignited.") if n == 1 else t("It ignited in {k} of them.", k=k))
        tone = "medium"
    elif k == 0 and n == 1:
        sentences.append(t("It did not ignite."))
        tone = "low"
    elif k == 0:
        sentences.append(t("It did not ignite in any of them."))
        tone = "low"
    else:
        sentences.append(t("It ignited in {k} of them.", k=k))
        tone = "medium"
    sentences.append(t("Test conditions: O₂ {o2}, pressure {p}.", o2=_fmt_range(s["oxygen_pct"], "%"), p=_fmt_range(s["pressure_kpa"], "kPa")))
    gravity_note = ""
    if env != "ISS":
        tone = "none"
        gravity_note = f"<span class='plain-badge warn'>{html.escape(t('These tests were in microgravity, not this environment.'))}</span>"
    links = " · ".join(f"<a href='{x['url']}' target='_blank'>{html.escape(x['short'])}, {t('p.')} {x['page']}</a>" for x in s["sources"])
    tone_label = {"medium": t("Ignited; spread not reported in this table"), "low": t("Did not ignite"), "none": t("No count shown")}[tone]
    map_part = f"<span class='plain-map'> → {html.escape(nm)}</span>" if nm != user_word else ""
    from src.access import say_button
    return (f"<div class='plain-card tone-{tone}'>{say_button(user_word + '. ' + ' '.join(sentences))}<div class='plain-title'>{html.escape(user_word)}{map_part}</div>"
            f"<div class='plain-sub'>{html.escape(t('Closest NASA-tested specimen, not your exact product.'))} "
            f"{html.escape(t('Separate verified table'))} · {html.escape(t('Flown on'))}: {html.escape(_platform(s['experiments'], _tr()))}</div>"
            f"<span class='plain-badge'>{html.escape(tone_label)}</span>{gravity_note}"
            f"<p>{html.escape(' '.join(sentences))}</p>{next_html(next_needed(key, None, env, s))}<div class='plain-sub'>{links}</div></div>"), tone


# Everyday things made of a similar kind of material. Illustration only: NASA tested the specimen, not these products.
EVERYDAY = {
    "pamuklu kumaş": (["cotton towels", "bed sheets", "cotton work clothes", "curtains"],
                      ["pamuklu havlular", "çarşaflar", "pamuklu iş kıyafetleri", "perdeler"]),
    "kablo kılıfı": (["phone charger cables", "headphone cables", "laptop power cords", "extension cords"],
                     ["telefon şarj kabloları", "kulaklık kabloları", "laptop güç kabloları", "uzatma kabloları"]),
    "kauçuk": (["silicone door and window seals", "phone cases", "baking mats", "watch straps"],
               ["silikon kapı ve pencere contaları", "telefon kılıfları", "fırın matları", "saat kayışları"]),
    "kağıt": (["notebooks", "checklists and manuals", "paper towels", "cardboard labels"],
              ["defterler", "kontrol listeleri ve kılavuzlar", "kâğıt havlular", "karton etiketler"]),
    "plastik (pmma)": (["acrylic windows", "display and screen covers", "light covers", "aquarium panels"],
                       ["akrilik pencereler", "ekran ve vitrin kapakları", "lamba kapakları", "akvaryum camları"]),
    "pmma_extra": (["acrylic windows", "display and screen covers", "light covers", "aquarium panels"],
                   ["akrilik pencereler", "ekran ve vitrin kapakları", "lamba kapakları", "akvaryum camları"]),
    "delrin_extra": (["small gears", "zipper pulls", "knobs and buttons", "kitchen utensil handles"],
                     ["küçük dişliler", "fermuar uçları", "düğmeler ve topuzlar", "mutfak gereci sapları"]),
    "hdpe_extra": (["water and milk bottles", "food storage boxes", "cutting boards", "bottle caps"],
                   ["su ve süt şişeleri", "yiyecek saklama kapları", "kesme tahtaları", "şişe kapakları"]),
    "nomex_extra": (["firefighter suits", "flight suits", "racing driver gloves", "fire-resistant work wear"],
                    ["itfaiyeci kıyafetleri", "uçuş tulumları", "yarış pilotu eldivenleri", "yanmaz iş kıyafetleri"]),
    "jersey_extra": (["T-shirts", "sportswear", "pyjamas", "underwear"],
                     ["tişörtler", "spor giyim", "pijamalar", "iç çamaşırları"]),
}


def everyday_html(key: str) -> str:
    """Chips with everyday examples, plus the honest caveat."""
    pair = EVERYDAY.get(key)
    if not pair:
        return ""
    items = pair[1] if _tr() else pair[0]
    chips = "".join(f"<span class='plain-badge'>{html.escape(x)}</span>" for x in items)
    return (f"<div class='plain-card tone-none' style='border-style:solid'>"
            f"<div class='plain-title' style='font-size:16px'> {html.escape(t('Everyday examples'))}</div>"
            f"<div style='margin:6px 0'>{chips}</div>"
            f"<div class='plain-sub'>{html.escape(t('Things made of a similar kind of material. NASA tested the specimen above, not these products.'))}</div></div>")


def everyday_words(key: str) -> str:
    """Search text: everyday examples and typed keywords for a specimen, both languages."""
    en, tr = EVERYDAY.get(key, ([], []))
    words = KEYWORDS.get(key, []) + EXTRA_KEYWORDS.get(key, [])
    return " ".join([*en, *tr, *words]).casefold()


def matches(key: str, label: str, query: str) -> bool:
    """Search by specimen name, everyday examples or keywords; word by word, so 'su şişesi' finds 'şişe'."""
    q = query.casefold().strip()
    if not q:
        return True
    text = (key + " " + label).casefold() + " " + everyday_words(key)
    if q in text:
        return True
    tokens = [w for w in q.replace(",", " ").split() if len(w) >= 3]
    return any(w in text or w[:-2] in text for w in tokens if len(w[:-2]) >= 3) or any(w in text for w in tokens)


NEXT_FOR_ENV = {"Moon Base": ("the same test in lunar gravity", "aynı testin Ay yerçekiminde yapılması"),
                "Mars Mission": ("a test in the Mars cabin atmosphere", "Mars kabin atmosferinde bir test"),
                "Earth Lab": ("a matching 1 g comparison test", "eşleşen bir 1 g karşılaştırma testi")}


def next_needed(key, rows, env: str, extra=None) -> str:
    """Rule-based gap: what evidence would close the biggest hole for this item. Describes missing data only."""
    tr = _tr()
    pick = (lambda en, trt: trt if tr else en)
    if key is None:
        return pick("a basic ignition and flame-spread test of this kind of item", "bu tür bir eşyanın temel tutuşma ve alev yayılma testi")
    if env == "Moon Base" and key in ("pamuklu kumaş", "plastik (pmma)", "pmma_extra"):
        return pick("a test on the lunar surface (simulated lunar-gravity results exist; FM² is planned)",
                    "Ay yüzeyinde bir test (benzetilmiş Ay yerçekimi sonuçları var; FM² planlı)")
    if env in NEXT_FOR_ENV:
        return pick(*NEXT_FOR_ENV[env])
    if extra is not None:
        if not extra.get("pressure_kpa"):
            return pick("the cabin pressure of the test reported", "testin kabin basıncının raporlanması")
        return pick("a measured flame-spread rate", "ölçülmüş bir alev yayılma hızı")
    if rows is None or rows.empty:
        return pick("a compiled count of NASA tests", "NASA testlerinin derlenmiş sayısı")
    if (rows.ignition == "disputed").any():
        return pick("a recount of the disputed ignition results", "çelişkili tutuşma sonuçlarının yeniden sayılması")
    if rows.oxygen_pct.isna().all():
        return pick("the oxygen level of the tests reported", "testlerin oksijen düzeyinin raporlanması")
    if rows.pressure_kpa.isna().all():
        return pick("the cabin pressure of the tests reported", "testlerin kabin basıncının raporlanması")
    if not (rows.propagation == "observed").any() and not (rows.propagation == "not_observed").any():
        return pick("a measured flame-spread result", "ölçülmüş bir alev yayılma sonucu")
    n = int(rows.test_count.fillna(0).sum())
    return pick(f"more repeat tests (only {n} so far)", f"daha fazla tekrar testi (şimdilik sadece {n})")


def next_html(text: str) -> str:
    return (f"<div class='plain-next'><b>{html.escape(t('Next evidence needed'))}:</b> {html.escape(text)}</div>")
