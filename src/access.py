"""Accessibility helpers: page language for screen readers, read-aloud buttons, plain-language glossary."""
import html

import streamlit as st

from src.i18n import t


def _tr() -> bool:
    return st.session_state.get("fg_lang", "EN") == "TR"


def set_page_language() -> None:
    """Tell screen readers which language the page is in (otherwise Turkish is read with English pronunciation)."""
    code = "tr" if _tr() else "en"
    st.html("<script>try{const d=window.parent.document.documentElement;"
            f"d.setAttribute('lang','{code}');d.setAttribute('translate','no');d.classList.add('notranslate');"
            "}catch(e){}</script>", unsafe_allow_javascript=True)


SAY_SCRIPT = """<script>try{
if(!window.parent.__fgSay){window.parent.__fgSay=true;
 const doc=window.parent.document;
 doc.addEventListener('click',function(e){
  const b=e.target.closest&&e.target.closest('.say-btn'); if(!b) return;
  const synth=window.parent.speechSynthesis; if(!synth) return;
  if(b.getAttribute('aria-pressed')==='true'){synth.cancel();b.setAttribute('aria-pressed','false');return;}
  synth.cancel();
  doc.querySelectorAll('.say-btn[aria-pressed=true]').forEach(x=>x.setAttribute('aria-pressed','false'));
  const u=new SpeechSynthesisUtterance(b.dataset.say); u.lang=b.dataset.lang; u.rate=0.95;
  const voice=synth.getVoices().find(v=>v.lang&&v.lang.toLowerCase().startsWith(b.dataset.lang.slice(0,2)));
  if(voice) u.voice=voice;
  u.onend=()=>b.setAttribute('aria-pressed','false');
  b.setAttribute('aria-pressed','true'); synth.speak(u);
 });
}}catch(e){}</script>"""

SAY_CSS = """<style>
.say-btn{float:right;margin:-2px 0 0 12px;min-height:40px;padding:6px 12px;border:1px solid var(--line,#314156);border-radius:6px;
  background:#17283d;color:#f3f6fb;font:600 14px Plex,sans-serif;cursor:pointer}
.say-btn:hover{border-color:#ffb36b}.say-btn[aria-pressed=true]{background:#3c281c;border-color:#ffb36b}
</style>"""


def enable_read_aloud() -> None:
    st.markdown(SAY_CSS, unsafe_allow_html=True)
    st.html(SAY_SCRIPT, unsafe_allow_javascript=True)


def say_button(text: str) -> str:
    """A real <button>: reachable with Tab, announced by screen readers, uses the browser's own offline voice."""
    lang = "tr-TR" if _tr() else "en-US"
    label = t("Read aloud")
    return (f"<button type='button' class='say-btn' aria-pressed='false' aria-label='{html.escape(label)}' "
            f"data-lang='{lang}' data-say='{html.escape(text, quote=True)}'> {html.escape(label)}</button>")


GLOSSARY = [
    (("Microgravity", "Mikroyerçekimi"),
     ("The near-weightless state in orbit, as on the ISS. Hot gas does not rise, so flames get no fresh air from below.",
      "ISS'teki gibi yörüngedeki neredeyse ağırlıksız ortam. Sıcak gaz yükselmez; bu yüzden aleve aşağıdan taze hava gelmez.")),
    (("Lunar / partial gravity", "Ay / kısmi yerçekimi"),
     ("About one sixth of Earth's gravity (≈0.16 g). Some flame tests imitate it with spinning rockets, centrifuges or parabolic flights.",
      "Dünya yerçekiminin yaklaşık altıda biri (≈0,16 g). Bazı alev testleri bunu dönen roketler, santrifüjler veya parabolik uçuşlarla taklit eder.")),
    (("Ignition", "Tutuşma"),
     ("The moment a material catches fire after being heated by an igniter.", "Bir malzemenin ısıtıcıyla ısıtıldıktan sonra alev aldığı an.")),
    (("Sustained burning", "Sürekli yanma"),
     ("The flame keeps burning after the igniter is switched off.", "Isıtıcı kapandıktan sonra da alevin yanmaya devam etmesi.")),
    (("Brief local flame", "Kısa yerel alev"),
     ("A small flame that appears only near the igniter and goes out quickly; it is not counted as sustained burning.",
      "Sadece ısıtıcının yanında görünen ve hemen sönen küçük alev; sürekli yanma sayılmaz.")),
    (("Flame spread", "Alev yayılması"),
     ("The flame moving along the material. Spread rate is how fast it moves, e.g. in mm/s.",
      "Alevin malzeme boyunca ilerlemesi. Yayılma hızı ne kadar hızlı ilerlediğidir, örneğin mm/s.")),
    (("Extinction / quench", "Sönme"),
     ("The flame goes out by itself, for example when airflow is too weak to feed it.",
      "Alevin kendiliğinden sönmesi; örneğin hava akışı alevi besleyemeyecek kadar zayıf olduğunda.")),
    (("Blow-off", "Üflenerek sönme"),
     ("The flame goes out because the airflow is too strong.", "Hava akışı fazla güçlü olduğu için alevin sönmesi.")),
    (("O₂ %", "O₂ %"),
     ("The share of oxygen in the air. Normal air is about 21%; more oxygen usually makes ignition easier.",
      "Havadaki oksijen oranı. Normal hava yaklaşık %21'dir; daha fazla oksijen genellikle tutuşmayı kolaylaştırır.")),
    (("kPa, psia, atm", "kPa, psia, atm"),
     ("Units of air pressure. 1 atm = 101.3 kPa = 14.7 psia (sea level). 8.2 psia ≈ 56.5 kPa.",
      "Hava basıncı birimleri. 1 atm = 101,3 kPa = 14,7 psia (deniz seviyesi). 8,2 psia ≈ 56,5 kPa.")),
    (("Specimen", "Numune"),
     ("The exact piece of material NASA burned. Results describe that specimen, not every product of the same kind.",
      "NASA'nın yaktığı malzeme parçasının kendisi. Sonuçlar o numuneyi anlatır, aynı türden her ürünü değil.")),
    (("SIBAL", "SIBAL"),
     ("A NASA test fabric of about 75% cotton and 25% fiberglass.", "Yaklaşık %75 pamuk ve %25 cam elyafından oluşan bir NASA test kumaşı.")),
    (("PMMA", "PMMA"),
     ("Acrylic plastic, also sold as Plexiglas.", "Akrilik plastik; pleksiglas olarak da bilinir.")),
    (("HDPE, Delrin, Nomex", "HDPE, Delrin, Nomex"),
     ("HDPE: the plastic of many bottles. Delrin: a hard plastic for small gears. Nomex: a fire-resistant fabric for flight suits.",
      "HDPE: birçok şişenin plastiği. Delrin: küçük dişliler için sert plastik. Nomex: uçuş tulumlarında kullanılan yanmaz kumaş.")),
    (("NTRS", "NTRS"),
     ("NASA Technical Reports Server, NASA's public library of technical reports. Every source link points there or to a NASA PDF.",
      "NASA Teknik Raporlar Sunucusu; NASA'nın herkese açık rapor kütüphanesi. Bütün kaynak bağlantıları oraya ya da bir NASA PDF'ine gider.")),
]


def glossary(expanded: bool = False) -> None:
    with st.expander(" " + t("Glossary · terms in plain words"), expanded=expanded):
        tr = _tr()
        rows = "".join(f"<dt>{html.escape(term[tr])}</dt><dd>{html.escape(text[tr])}</dd>" for term, text in GLOSSARY)
        st.markdown("<style>.fg-glossary dt{font-weight:600;margin-top:10px}.fg-glossary dd{margin:2px 0 0 0;color:var(--muted,#abbace)}</style>"
                    f"<dl class='fg-glossary'>{rows}</dl>", unsafe_allow_html=True)


def chart_table(frame) -> None:
    """Text alternative for a chart: the same numbers as a table, for screen readers and keyboard users."""
    from src.ui import dataframe
    with st.expander(t('Accessible chart data')):
        dataframe(frame)
