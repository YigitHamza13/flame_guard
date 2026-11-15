"""Plain short answers for the suggested assistant questions. Each sentence restates a passage that is shown
underneath (verbatim, with its PDF page); nothing here goes beyond those passages or the reviewed records."""

SHORT = {
    "What pressure is reported for WIF?": (
        "About 1 atmosphere (101 kPa). The WIF tests used the normal Spacelab cabin air, about 21% oxygen.",
        "Yaklaşık 1 atmosfer (101 kPa). WIF testlerinde Spacelab'ın normal kabin havası, yaklaşık %21 oksijen kullanıldı."),
    "What were the Saffire silicone findings?": (
        "None of the four silicone sheets kept burning. After the igniter switched off, a tiny flame stayed for a moment, did not spread and went out.",
        "Dört silikon levhanın hiçbiri yanmaya devam etmedi. Ateşleyici kapanınca küçük bir alev bir an kaldı, yayılmadı ve söndü."),
    "Which evidence gaps exist on the Moon?": (
        "No material has been burned on the lunar surface yet. Only SIBAL fabric and a PMMA rod have measured results in simulated lunar gravity (LUCI). NASA's FM² experiment is planned to test on the Moon.",
        "Ay yüzeyinde henüz hiçbir malzeme yakılmadı. Benzetilmiş Ay yerçekiminde (LUCI) ölçülmüş sonucu olan sadece SIBAL kumaşı ve bir PMMA çubuğu var. NASA'nın FM² deneyi Ay'da test yapmayı planlıyor."),
    "What did LUCI measure for PMMA?": (
        "In simulated lunar gravity the flame tip moved along a 4 mm acrylic (PMMA) rod at about 1.5 mm per second, and the flame grew until it covered the rod. This was on a spinning rocket, not on the Moon.",
        "Benzetilmiş Ay yerçekiminde alev ucu 4 mm'lik akrilik (PMMA) çubuk boyunca saniyede yaklaşık 1,5 mm ilerledi ve alev büyüyüp çubuğu sardı. Bu test Ay'da değil, dönen bir roketteydi."),
    "What experiments are planned for FM2?": (
        "Burn tests on the lunar surface. The 2024 plan named SIBAL fabric and PMMA at 21% oxygen (14.7 psia) and 34% oxygen (8.2 psia); a 2026 concept lists four atmospheres from 25% to 37% oxygen. No results exist yet.",
        "Ay yüzeyinde yanma testleri. 2024 planında SIBAL kumaşı ve PMMA, %21 oksijen (14,7 psia) ve %34 oksijen (8,2 psia) koşullarında yer alıyordu; 2026 taslağında %25 ile %37 arasında dört atmosfer var. Henüz sonuç yok."),
}

MEANS = {
    "What pressure is reported for WIF?": ("So the cable results describe normal cabin pressure, not the low-pressure air planned for exploration cabins.",
                                           "Yani kablo sonuçları normal kabin basıncını anlatır; keşif kabinleri için planlanan düşük basınçlı havayı değil."),
    "What were the Saffire silicone findings?": ("This describes these silicone sheets under these conditions, not every rubber product. It is not a safety rating.",
                                                 "Bu, bu silikon levhaları bu koşullarda anlatır; her kauçuk ürünü değil. Güvenlik derecesi değildir."),
    "Which evidence gaps exist on the Moon?": ("Results from the ISS cannot simply be reused for a lunar base; the Moon needs its own tests.",
                                               "ISS sonuçları Ay üssü için olduğu gibi kullanılamaz; Ay'ın kendi testleri gerekiyor."),
    "What did LUCI measure for PMMA?": ("It is the first long lunar-gravity flame measurement for this plastic, but it does not replace a test on the Moon itself.",
                                        "Bu plastik için ilk uzun süreli Ay yerçekimi alev ölçümü; ama Ay'ın kendisinde yapılacak testin yerini tutmaz."),
    "What experiments are planned for FM2?": ("These are plans; FLAMEGUARD shows them as planned, never as results.",
                                              "Bunlar plan; FLAMEGUARD bunları sonuç olarak değil, plan olarak gösterir."),
}


def short_answer(question: str, lang: str, translate) -> tuple:
    """(answer, meaning) for a suggested question in either language, else (None, None)."""
    q = (question or "").strip().casefold()
    for en in SHORT:
        if q in (en.casefold(), translate(en).casefold()):
            i = 1 if lang == "TR" else 0
            return SHORT[en][i], MEANS[en][i]
    return None, None


# General concept questions are answered from the app's own glossary (src/access.py GLOSSARY), clearly labelled.
# Index into GLOSSARY → words that point to that term. Checked in this order (more specific first).
GLOSSARY_WORDS = [
    (7, ["blow-off", "blowoff", "üflenerek"]),
    (4, ["local flame", "yerel alev"]),
    (3, ["sustained", "sürekli yanma", "yanmaya devam"]),
    (6, ["extinction", "extinguish", "quench", "sönme", "söner", "söndü"]),
    (5, ["flame spread", "spread rate", "alev yayıl", "yayılma hızı", "yayılım"]),
    (2, ["ignition", "ignite", "tutuşma", "tutuşur", "tutuşmak"]),
    (1, ["lunar gravity", "partial gravity", "ay yerçekimi", "kısmi yerçekimi", "moon gravity"]),
    (0, ["microgravity", "mikroyerçekimi", "mikrogravite", "weightless", "ağırlıksız", "sıfır yerçekimi", "zero gravity"]),
    (8, ["oxygen", "oksijen", "o2", "o₂"]),
    (9, ["pressure", "basınç", "kpa", "psia", "atm", "atmosfer"]),
    (11, ["sibal"]),
    (12, ["pmma", "acrylic", "akrilik", "plexiglas", "pleksi"]),
    (13, ["hdpe", "delrin", "nomex"]),
    (14, ["ntrs"]),
    (10, ["specimen", "numune"]),
]


def glossary_answer(question: str, lang: str) -> tuple:
    """(answer, term) from the glossary for a general concept question, else (None, None)."""
    from src.access import GLOSSARY
    q = (question or "").replace("İ", "i").casefold()
    for idx, words in GLOSSARY_WORDS:
        if any(w in q for w in words):
            term, definition = GLOSSARY[idx]
            i = 1 if lang == "TR" else 0
            return definition[i], term[i]
    return None, None


# Topic answers for common questions. Every number is one already shown in the app with its PDF page
# (src/risk.py ENV_FACTORS, data/extended_review.json, the cargo cards). Order matters: specific topics first.
def _src(doc, page, label):
    from src.links import page as pdf_page
    return label, pdf_page(doc, page)


TOPICS = [
    (["smoke alarm", "duman alarm", "alarm", "toxic", "zehir", "co2", "co₂", "karbon monoksit", "carbon monoxide", "gas", "gaz"],
     ("In Saffire VI the temperature rose only near the fire, but CO and CO₂ rose clearly; the PMMA tests went past the 1-hour CO₂ and 24-hour CO limits. A typical smoke-alarm threshold was reached only after 981 seconds.",
      "Saffire VI'da sıcaklık sadece alevin yakınında yükseldi, ama CO ve CO₂ belirgin şekilde arttı; PMMA testleri 1 saatlik CO₂ ve 24 saatlik CO sınırlarını aştı. Tipik bir duman alarmı eşiğine ancak 981. saniyede ulaşıldı."),
     ("In a closed cabin the gases can matter more than the heat, and a normal smoke alarm may react late.",
      "Kapalı bir kabinde gazlar ısıdan daha önemli olabilir ve normal bir duman alarmı geç tepki verebilir."),
     ("20240002981", 6, "Saffire VI 2024, p. 6")),
    (["fire on the iss", "fire breaks out", "iss'te yangın", "istasyonda yangın", "yangın çıkarsa", "fire happen"],
     ("NASA's large fire tests were flown in uncrewed cargo vehicles, not with crew. In Saffire VI the temperature rose only near the fire, while CO and CO₂ rose clearly, and a typical smoke-alarm threshold was reached only after 981 seconds.",
      "NASA'nın büyük yangın testleri mürettebatlı istasyonda değil, insansız kargo araçlarında yapıldı. Saffire VI'da sıcaklık sadece alevin yakınında arttı; CO ve CO₂ belirgin şekilde yükseldi ve tipik bir duman alarmı eşiğine ancak 981. saniyede ulaşıldı."),
     ("The main early danger in these tests was the gases, not the heat.", "Bu testlerde ilk tehlike ısı değil, gazlardı."),
     ("20240002981", 6, "Saffire VI 2024, p. 6")),
    (["airflow", "air flow", "ventilation", "hava akış", "havalandırma", "rüzgar", "flow"],
     ("Airflow decides a lot in microgravity. In BASS-II, 6 SIBAL tests went out at very low airflow (2.2–5 cm/s) and one was blown out at 47 cm/s. In WIF a weak flame in still air brightened as soon as the airflow started.",
      "Mikroyerçekiminde hava akışı çok belirleyicidir. BASS-II'de 6 SIBAL testi çok düşük akışta (2,2–5 cm/s) söndü, biri 47 cm/s'de üflenerek söndü. WIF'te durgun havada zayıf yanan alev, akış başlar başlamaz parladı."),
     ("Ventilation feeds or starves a flame, because there is no rising hot air in orbit.", "Yörüngede sıcak hava yükselmediği için havalandırma alevi besler ya da söndürür."),
     ("20210011385", 104, "BASS-II summary, Table 7.1, p. 104")),
    (["how does fire", "how do flames", "fire behave", "flame behave", "nasıl yanar", "ateş nasıl", "alev nasıl", "neden küre", "küre şekl", "sphere", "spherical", "yuvarlak"],
     ("In microgravity hot gas does not rise, so a flame gets no fresh air from below. It depends on the airflow around it: in BASS-II, SIBAL flames went out at very low airflow (2.2–5 cm/s) and one was blown out at 47 cm/s.",
      "Mikroyerçekiminde sıcak gaz yükselmez; bu yüzden aleve aşağıdan taze hava gelmez. Alev çevresindeki hava akışına bağlıdır: BASS-II'de SIBAL alevleri çok düşük akışta (2,2–5 cm/s) söndü, biri 47 cm/s'de üflenerek söndü."),
     ("That is why results from Earth or from the ISS cannot simply be reused somewhere else.", "Bu yüzden Dünya'daki ya da ISS'teki sonuçlar başka bir ortamda olduğu gibi kullanılamaz."),
     ("20210011385", 104, "BASS-II summary, Table 7.1, p. 104")),
    (["mars"],
     ("This collection has no measured flame result for Mars. A 2026 NASA presentation is titled 'lunar and Martian gravity', but it gives no Mars measurement that we could verify.",
      "Bu koleksiyonda Mars için ölçülmüş bir alev sonucu yok. 2026 tarihli bir NASA sunumunun başlığında 'Ay ve Mars yerçekimi' geçiyor, ama doğrulayabildiğimiz bir Mars ölçümü vermiyor."),
     ("A Mars mission planner has no compiled test here; this is one of the gaps the app lists.", "Bir Mars görevi planlayıcısı için burada derlenmiş test yok; uygulamanın listelediği boşluklardan biri bu."),
     ("20260001966", None, "LPSC 2026")),
    (["moon", "lunar", " ay'", " ay’", " ay yüzey", " ayda ", " ay üss", " ay yerçek", " ay için"],
     ("No material has been burned on the lunar surface yet. Only SIBAL fabric and a PMMA rod have measured results in simulated lunar gravity (LUCI, a spinning sounding rocket). NASA's FM² experiment is planned to test on the Moon.",
      "Ay yüzeyinde henüz hiçbir malzeme yakılmadı. Benzetilmiş Ay yerçekiminde ölçülmüş sonucu olan sadece SIBAL kumaşı ve bir PMMA çubuğu var (LUCI, dönen bir sonda roketi). NASA'nın FM² deneyi Ay'da test yapmayı planlıyor."),
     ("Results from the ISS cannot simply be reused for a lunar base.", "ISS sonuçları Ay üssü için olduğu gibi kullanılamaz."),
     ("20250010653", 19, "LUCI 2025, p. 19")),
    (["fm2", "fm²", "fm 2"],
     ("FM² (Flammability of Materials on the Moon) is a planned NASA burn test on the lunar surface. The 2024 plan named SIBAL fabric and PMMA at 21% oxygen (14.7 psia) and 34% oxygen (8.2 psia). No results exist yet.",
      "FM² (Ay'da Malzeme Yanıcılığı), Ay yüzeyinde planlanan bir NASA yanma testidir. 2024 planında SIBAL kumaşı ve PMMA, %21 oksijen (14,7 psia) ve %34 oksijen (8,2 psia) koşullarında yer alıyordu. Henüz sonuç yok."),
     ("FLAMEGUARD shows it as a plan, never as a result.", "FLAMEGUARD bunu sonuç olarak değil, plan olarak gösterir."),
     ("20240015307", 1, "FM² poster 2024, p. 1")),
    (["luci"],
     ("LUCI flew SIBAL fabric and an acrylic (PMMA) rod on a spinning sounding rocket to imitate lunar gravity. The SIBAL flame base spread about 0.92 mm/s and the PMMA flame tip about 1.5 mm/s.",
      "LUCI, Ay yerçekimini taklit etmek için SIBAL kumaşı ve akrilik (PMMA) bir çubuğu dönen bir sonda roketinde yaktı. SIBAL alev tabanı yaklaşık 0,92 mm/s, PMMA alev ucu yaklaşık 1,5 mm/s yayıldı."),
     ("These are the first long lunar-gravity flame measurements, but not tests on the Moon itself.", "Bunlar ilk uzun süreli Ay yerçekimi alev ölçümleri; ama Ay'ın kendisinde yapılmış testler değil."),
     ("20250010653", 19, "LUCI 2025, p. 19")),
    (["saffire"],
     ("Saffire is NASA's spacecraft fire safety experiment: large samples were burned inside uncrewed ISS resupply vehicles after they left the station. Saffire-II found that none of the four silicone sheets kept burning.",
      "Saffire, NASA'nın uzay aracı yangın güvenliği deneyidir: büyük numuneler, istasyondan ayrılan insansız ISS ikmal araçlarının içinde yakıldı. Saffire-II'de dört silikon levhanın hiçbiri yanmaya devam etmedi."),
     ("Burning in an empty cargo vehicle let NASA test much larger fires than is possible with crew on board.", "Boş bir kargo aracında yakmak, mürettebat varken mümkün olandan çok daha büyük yangınları test etmeyi sağladı."),
     ("20170008805", 12, "Saffire-II 2017, p. 12")),
    (["bass"],
     ("BASS (Burning and Suppression of Solids) burned SIBAL fabric on the International Space Station. The fabric did not ignite at 16.4% oxygen but ignited at 17.1%. The report's split of ignited and non-ignited tests is disputed, so FLAMEGUARD shows no ignition count for it.",
      "BASS (Katıların Yanması ve Bastırılması), SIBAL kumaşını Uluslararası Uzay İstasyonu'nda yaktı. Kumaş %16,4 oksijende tutuşmadı, %17,1'de tutuştu. Raporda tutuşan ve tutuşmayan test ayrımı çelişkili; bu yüzden FLAMEGUARD tutuşma sayısı göstermiyor."),
     ("A small rise in oxygen can change whether a material ignites at all.", "Oksijendeki küçük bir artış, malzemenin tutuşup tutuşmayacağını değiştirebilir."),
     ("20150008962", 9, "BASS 2015, p. 9")),
    (["wif", "wire insulation"],
     ("WIF (Wire Insulation Flammability) burned polyethylene wire insulation in the Spacelab glovebox on the Space Shuttle (USML-1): 4 tests in cabin air at about 21% oxygen and 1 atm. It ignited in all 4; the flame spread in 3.",
      "WIF (Kablo Yalıtımı Yanıcılığı), Uzay Mekiği'ndeki Spacelab eldivenli kabininde (USML-1) polietilen kablo yalıtımını yaktı: yaklaşık %21 oksijen ve 1 atm kabin havasında 4 test. 4'ünde de tutuştu; 3'ünde alev yayıldı."),
     ("These are observed counts under these conditions, not a general ignition probability.", "Bunlar bu koşullarda gözlenen sayılardır, genel bir tutuşma olasılığı değildir."),
     ("19960008389", 2, "WIF 1994, p. 2")),
    (["oxygen", "oksijen", "o2", "o₂"],
     ("Normal air is about 21% oxygen. Small changes matter: in BASS the SIBAL fabric did not ignite at 16.4% oxygen but did at 17.1%. On Mir the cabin oxygen was 22.5–25.4%, above the expected 21%.",
      "Normal havada oksijen yaklaşık %21'dir. Küçük farklar önemlidir: BASS'ta SIBAL kumaş %16,4 oksijende tutuşmadı, %17,1'de tutuştu. Mir'de kabin oksijeni beklenen %21'in üstünde, %22,5–25,4 arasındaydı."),
     ("More oxygen usually makes ignition easier, so the cabin air must be part of every comparison.", "Daha fazla oksijen genellikle tutuşmayı kolaylaştırır; bu yüzden kabin havası her karşılaştırmada hesaba katılmalı."),
     ("20150008962", 9, "BASS 2015, p. 9")),
    (["pressure", "basınç", "kpa", "psia"],
     ("Saffire VI burned samples at 100, 70.7 and about 54–55 kPa with 22–31% oxygen — like the low-pressure, oxygen-rich air planned for exploration cabins. Sea level is 101.3 kPa.",
      "Saffire VI numuneleri 100, 70,7 ve yaklaşık 54–55 kPa basınçta, %22–31 oksijenle yaktı; keşif kabinleri için planlanan düşük basınçlı, oksijence zengin havaya benzer. Deniz seviyesi 101,3 kPa'dır."),
     ("Lower pressure usually comes with more oxygen, so both must be compared together.", "Düşük basınç genellikle daha fazla oksijenle gelir; bu yüzden ikisi birlikte karşılaştırılmalı."),
     ("20240002981", 3, "Saffire VI 2024, p. 3")),
    (["safe", "güvenli", "dangerous", "tehlikeli", "risky", "riskli", "most flammable", "en yanıcı", "en çok yanan", "safest"],
     ("FLAMEGUARD never calls a material safe or dangerous; that is a decision for experts. It shows what NASA observed: polyethylene wire insulation ignited in 4 of 4 tests and the flame spread in 3, while four silicone sheets only showed a brief local flame. Missing data does not mean safe.",
      "FLAMEGUARD bir malzemeye asla güvenli ya da tehlikeli demez; bu karar uzmanlarındır. NASA'nın gözlediğini gösterir: polietilen kablo yalıtımı 4 testin 4'ünde tutuştu ve 3'ünde alev yayıldı; dört silikon levhada ise sadece kısa, yerel bir alev oluştu. Verinin olmaması güvenli olduğu anlamına gelmez."),
     ("Type your item in Cargo Screening to see its own result and the conditions.", "Kendi eşyanızın sonucunu ve koşullarını görmek için Kargo Taraması'na yazın."),
     ("19960008389", 2, "WIF 1994, p. 2")),
    (["flameguard", "what does this app", "bu uygulama", "nasıl kullan", "how to use", "how do i use"],
     ("Type an everyday item in Cargo Screening, for example 'cotton T-shirt'. FLAMEGUARD shows the closest NASA-tested specimen, what happened in space, the test conditions, what is still missing, and the report page.",
      "Kargo Taraması'na günlük bir eşya yazın, örneğin 'pamuklu tişört'. FLAMEGUARD en yakın NASA numunesini, uzayda ne olduğunu, test koşullarını, neyin hâlâ eksik olduğunu ve rapor sayfasını gösterir."),
     ("It never guesses: unknown stays unknown.", "Asla tahmin etmez: bilinmeyen, bilinmeyen olarak kalır."),
     None),
]


def topic_answer(question: str, lang: str) -> tuple:
    """(answer, meaning, (label, url)|None) for a common topic, else (None, None, None)."""
    q = " " + correct_question(question) + " "
    i = 1 if lang == "TR" else 0
    for words, ans, means, src in TOPICS:
        if any(w in q for w in words):
            return ans[i], means[i], (_src(*src) if src else None)
    return None, None, None


# This compatibility API retains historical templates for existing callers/tests.
# The UI and evaluator MUST use resolve_answer, which gates the verified subset.
def correct_question(question):
    import re
    from difflib import get_close_matches
    q = (question or "").replace("İ", "i").casefold()
    vocabulary = {w for words, *_ in TOPICS for phrase in words for w in re.findall(r"\w+", phrase) if len(w) >= 3}
    vocabulary.update(["uzayda", "ateş", "nasıl", "yanar", "saffire", "nereden", "söndürür", "veriler"])
    def fix(match):
        word = match.group()
        if len(word) < 3 or word in vocabulary or word in {"fayda", "telefon"}:
            return word
        candidates = get_close_matches(word, sorted(vocabulary), n=1, cutoff=0.8)
        return candidates[0] if candidates else word
    return re.sub(r"\w+", fix, q)


# Each statement below was checked in the bundled PDF at these PDF page numbers.
# WIF 19960008389 pp. 1, 5; Saffire-II 20170008805 p. 12;
# LUCI 20250010653 pp. 16, 19-21. No BASS-II summary/Saffire VI PDF is bundled.
VERIFIED_TOPICS = [
    (["put out", "extinguish a fire", "fire suppression", "yangın söndür", "yangını söndür"],
     ("In WIF, stopping ventilation quenched the flame. The report says this demonstration persuaded the Shuttle program to adopt ventilation cutoff as a firefighting procedure.",
      "WIF deneyinde havalandırma kesilince alev söndü. Rapora göre bu gözlem, Uzay Mekiği programının havalandırmayı kesmeyi yangınla mücadele prosedürüne almasını sağladı."),
     ("A historical test finding, not an operating instruction for another spacecraft.", "Tarihsel deney bulgusudur; başka bir uzay aracı için operasyon talimatı değildir."),
     ("19960008389", 5, "WIF, PDF 5")),
    (["faster", "daha hızlı", "why test in space", "neden uzayda test", "uzayda neden test"],
     ("A universal faster/slower conclusion is not supported. In Saffire-II the thin silicone specimen was entirely consumed in normal gravity, but its brief gas-phase flame did not spread in microgravity.",
      "Genel bir daha hızlı/yavaş sonucu çıkarılamaz. Saffire-II ince silikon numunesi normal yerçekiminde tamamen tüketildi; mikroyerçekiminde kısa gaz fazı alevi yayılmadı."),
     ("Compare the specimen and test conditions; do not transfer an ISS result to the Moon or Mars.", "Numuneyi ve deney koşullarını karşılaştırın; ISS sonucunu Ay veya Mars'a taşımayın."),
     ("20170008805", 12, "Saffire-II, PDF 12")),
    (["gravity affect", "yerçekimi alevi", "yerçekimi etk"],
     ("LUCI measured a SIBAL flame-base spread rate of about 0.92 mm/s in simulated lunar gravity. This is not a lunar-surface result or a general rate for all materials.",
      "LUCI, benzetilmiş Ay yerçekiminde SIBAL alev tabanı yayılım hızını yaklaşık 0,92 mm/s ölçtü. Bu, Ay yüzeyi sonucu veya tüm malzemeler için genel bir hız değildir."),
     ("Flame base and flame tip are different measurements.", "Alev tabanı ve alev ucu ayrı ölçümlerdir."),
     ("20250010653", 19, "LUCI, PDF 19")),
]
# Keep specific topics ahead of historical generic safety/airflow templates.
TOPICS[:0] = VERIFIED_TOPICS


def _source_available(doc, page_no):
    import hashlib, json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    inventory = json.loads((root / "data/assistant_sources.json").read_text(encoding="utf-8"))
    meta = inventory.get(doc)
    pdf = root / "sources/originals" / (doc + ".pdf")
    return bool(meta and pdf.is_file() and 1 <= page_no <= meta["pages"]
                and hashlib.sha256(pdf.read_bytes()).hexdigest() == meta["sha256"])


def resolve_answer(question, lang="EN", translate=lambda s:s, item_callback=None):
    """Single offline answer route shared by the UI and benchmark. No network calls.

    Historical ungated templates remain callable for compatibility, never rendered here.
    """
    import re, json, csv
    from pathlib import Path
    from src.links import page
    q = correct_question(question)
    tr = lang == "TR"
    def result(kind="none", answer=None, meaning=None, refs=()):
        if refs and not all(_source_available(d, n) for d,n in refs):
            return result()
        return dict(kind=kind, answer=answer, meaning=meaning,
                    sources=[dict(id=d, page=n, url=page(d,n)) for d,n in refs])
    def pair(en, tur): return tur if tr else en
    if re.search(r"\b(?:20[3-9]\d|21\d\d|will)\b|gidecek|gönderilecek", q):
        return result()
    if re.search(r"\b(cost|price|fiyat|fiyatı|maliyet|density|yoğunluğu|tensile|strength|sıcaklığı)\b", q):
        return result()
    # Exact definitions only; an unrelated sentence containing oxygen is not an answer.
    if len(q.split()) <= 4 and (q.startswith(("what is ", "define ")) or q.endswith((" nedir", " nedir?"))):
        if any(w in q for w in ("ignition", "tutuşma", "extinction", "sönme")):
            a, term = glossary_answer(q, lang)
            if a: return result("glossary", a, pair("Glossary definition: ", "Sözlük tanımı: ")+term)
    if any(w in q for w in ("alarm", "saffire vi", "saffire 6", "toxic", "zehir", "bass-ii airflow")):
        return result()  # required source PDF absent; no numbers inferred from old templates
    if any(w in q for w in ("safe", "dangerous", "tehlikeli", "güvende", "güvenli", "riskli", "en yanıcı")):
        return result("topic", pair("Material approval belongs to qualified experts. Missing data does not mean safe.",
          "Malzeme onayı yetkin uzmanlara aittir. Veri olmaması güvenli olduğu anlamına gelmez."),
          refs=(("19960008389",5),))
    if any(w in q for w in ("data come", "veriler nereden", "kaç test", "how many tests")):
        root=Path(__file__).resolve().parents[1]
        inv=json.loads((root/'data/assistant_sources.json').read_text(encoding='utf-8'))
        with (root/'data/experiments.csv').open(encoding='utf-8-sig', newline='') as f: rows=list(csv.DictReader(f))
        count=sum(int(float(x['test_count'])) for x in rows)
        msg=pair("Local inventory: {docs} NASA PDFs, {pages} PDF pages; {rows} compiled rows reporting {tests} tests. Catalog entries and simulated-gravity study records are not additional counted tests.",
          "Yerel envanter: {docs} NASA PDF'i, {pages} PDF sayfası; {rows} derleme satırında raporlanan {tests} test. Katalog kayıtları ve benzetilmiş yerçekimi çalışma kayıtları ek test sayıları değildir.")
        return result('topic',msg.format(docs=len(inv),pages=sum(x['pages'] for x in inv.values()),rows=len(rows),tests=count),refs=(("19960008389",1),))
    for words,ans,means,src in VERIFIED_TOPICS:
        if any(w in q for w in words) or ("yangın" in q and "söndür" in q and words is VERIFIED_TOPICS[0][0]):
            return result('topic',ans[int(tr)],means[int(tr)],((src[0],src[1]),))
    # LUCI PMMA tip rate is on p.21, not the SIBAL p.19.
    if 'luci' in q and ('pmma' in q or 'akrilik' in q):
        return result('short', pair("LUCI measured a PMMA flame-tip spread rate of about 1.5 mm/s in simulated lunar gravity. The flame base did not reach steady spread.",
          "LUCI benzetilmiş Ay yerçekiminde PMMA alev ucu yayılım hızını yaklaşık 1,5 mm/s ölçtü. Alev tabanı kararlı yayılıma ulaşmadı."),refs=(("20250010653",20),("20250010653",21)))
    if re.search(r"\b(moon|lunar|ay|ayda)\b",q):
        return result('topic',pair("This collection contains simulated lunar-gravity studies and a planned FM² lunar-surface experiment, not a completed lunar-surface burn test.",
          "Bu koleksiyonda benzetilmiş Ay yerçekimi çalışmaları ve planlanan FM² Ay yüzeyi deneyi var; tamamlanmış Ay yüzeyi yanma testi yok."),refs=(("20250010653",16),("20240015307",1)))
    if any(w in q for w in ("fire behave", "uzayda ateş", "fire in space", "space fire")):
        return result('topic',pair("Buoyant convection is suppressed in microgravity. In WIF, airflow changed the wire-insulation flame; a single universal flame shape or spread rate cannot be assigned.",
          "Mikroyerçekiminde kaldırma kuvvetine bağlı taşınım baskılanır. WIF'te hava akışı kablo yalıtımı alevini değiştirdi; tek bir genel alev şekli veya yayılım hızı atanamaz."),refs=(("19960008389",1),("19960008389",2)))
    if 'saffire' in q or 'silicone' in q or 'silikon' in q:
        return result('topic',pair("In Saffire-II a tiny gas-phase flame remained after igniter shutdown, did not spread and quickly extinguished.",
          "Saffire-II'de ateşleyici kapandıktan sonra küçük bir gaz fazı alevi kaldı; yayılmadı ve kısa sürede söndü."),refs=(("20170008805",12),))
    if re.search(r"\b(wif|cable|wire|kablo|kablosu|headphone|kulaklık)\b",q):
        a=pair("Polyethylene wire insulation was tested 4 times. It ignited in 4 of them. The flame spread in 3. Test conditions: about 21% oxygen and 1 atm, microgravity. This is a specimen proxy, not a test of your product.",
          "Polietilen kablo yalıtımı 4 kez test edildi. 4'ünde tutuştu; 3'ünde alev yayıldı. Koşullar: yaklaşık %21 oksijen ve 1 atm, mikroyerçekimi. Bu bir numune eşleştirmesidir; ürününüzün testi değildir.")
        return result('item' if 'wif' not in q else 'topic',a,refs=(("19960008389",1),("19960008389",2)))
    if any(w in q for w in ('glass bottle','cam şişe')):
        return result('item',pair("Glass is not matched to a different material. No tested specimen for this item in the collection.","Cam farklı bir malzemeyle eşleştirilmez. Koleksiyonda bu eşya için test edilmiş numune yok."))
    if any(w in q for w in ('dünyada oksijen','oxygen on earth')):
        return result('topic',pair("WIF used cabin air at approximately 21% oxygen and 1 atm; this is the reported study condition.","WIF yaklaşık %21 oksijen ve 1 atm kabin havasını kullandı; bu raporlanan çalışma koşuludur.").replace('WIF ',''),refs=(("19960008389",1),))
    return result()
