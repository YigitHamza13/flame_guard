# FLAMEGUARD — NASA space-fire evidence, made accessible

**NASA Space Apps Challenge 2026 · Ankara · Challenge: *Flame in Freefall* · Team: BeatlessFlame**
Team members: *(add names and roles here)*

> Türkçe özet aşağıda · Turkish summary below

## The problem
Fire behaves differently in space. Without gravity there is no rising hot air, so flames spread, smoulder and go out in
ways Earth tests do not predict. NASA has flown many combustion experiments, but the results sit in long technical
reports. Anyone who asks *"has something like my cargo ever been burned in space?"* must read hundreds of PDF pages.

## What FLAMEGUARD does
1. **Pick an environment:** ISS, lunar habitat, Mars mission or an Earth laboratory.
2. **Type your cargo** in your own words — *cotton t-shirt, cable, rubber seal, notebook* — or pick a NASA specimen.
3. **Read one plain sentence per item**, for example: *"NASA tested this specimen in space 4 times. It ignited in 4 of them. The flame spread in 3."*
   Each item is matched to the **closest NASA-tested specimen** and the card says that it is not your exact product.
4. **Check the risk factor tables:** one row per cargo item (ignition, sustained burning, flame spread, extinction, tested O₂ and
   pressure, same gravity or not) and five cabin factors NASA observed — oxygen, airflow, smoke and toxic gases, pressure, gravity —
   each with its report page. Words and sources only, never a score.
5. **Open the source:** every result links to the NASA report page it came from. Exports (CSV, JSON, research brief) keep the sources.

When there is no data, FLAMEGUARD says so. It never estimates a missing value and never calls a material safe.
Card colours and the page tint (soft red-orange when flame spread was observed) are reading aids, explained on screen, not safety ratings.

## Why this makes space data accessible
- **Plain language first**, technical detail one click away.
- **Everyday examples:** each NASA specimen lists familiar things made of a similar material (charger cables, water bottles,
  gaskets, T-shirts…), and Material Explorer can be searched with those everyday words.
- **The assistant answers in Turkish too:** quotes stay in NASA's original English, with a plain summary in the selected language.
- **English and Turkish**, from JSON language files; adding a language is one more file.
- **Not by colour alone:** every colour comes with words and a legend.
- **Offline:** NASA PDFs, extracted pages and NASA 3D models are packaged; no account or API key is needed.
- **Honest gaps:** the app shows where evidence is missing, such as lunar-surface tests, which are still only planned.

## Data
| | |
|---|---|
| Compiled NASA test rows | 11 rows, 39 reported tests (SIBAL fabric, polyethylene wire, Saffire-II silicone, Mir paper) |
| Lunar-gravity study records | 7 (5 measured with simulated or short-duration lunar gravity, 2 planned) |
| Extra verified specimens | 5 (PMMA, Delrin, HDPE, Nomex, cotton jersey; 16 tests from Mir FFFT and Saffire VI), kept in a separate table |
| NASA PSI catalog records | 26 (metadata) |
| NASA documents packaged | 9 PDFs, with page references and SHA-256 hashes |

Rules: values come only from the cited PDF page; missing values stay empty; disputed counts (SIBAL ignition) are shown
as disputed; a brief local gas flame is not counted as sustained burning. Default mission atmospheres are labelled as
assumptions (ISS: about 21% O₂, 1 atm; lunar habitat: NASA's planned FM² atmosphere, 34% O₂ at 8.2 psia, poster
20240015307 p. 1) and can be changed on the Environments page.

## AI use
- **In the app:** the research assistant searches the packaged NASA passages locally. Optional Gemini excerpt selection is off by default; when enabled, only public passages and the question are sent.
- **In development:** AI coding assistants helped write code and cross-check data against the PDFs.

## Run
Python 3.12:
```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Validate and package
```sh
python -m unittest discover -s tests -v
python scripts/package_release.py
```
Tests cover source integrity, lossless imports, counts, assumptions, exports, malformed AI responses, both languages and all eight pages.
Packaging uses an allowlist and never includes `.env`; only `.env.example` is shipped.

## Deployment

Deployment-ready update: 3D models load automatically when their view opens. No manual model download/load step is shown. The local poster remains visible until the model is ready; retry is offered only after an error. See [deployment instructions](docs/DEPLOYMENT.md).

Streamlit hosting: choose `app.py` and `requirements.txt`, keep `data/` writable (SQLite is built on first run), and set any secrets in the host.
Docker is also supported (`docker build -t flameguard .` then `docker run --rm -p 8501:8501 flameguard`).
See [validation and operating notes](docs/VALIDATION.md).

## Limits
- Independent student project; not NASA-approved and not a flight-safety assessment.
- Each result describes a specific NASA specimen, not a whole material category.
- Lunar-gravity results come from sounding rockets, centrifuges and parabolic flights, not from the lunar surface.

---

## Türkçe özet
FLAMEGUARD, NASA'nın uzayda yaptığı yangın deneylerini herkesin okuyabileceği hâle getirir. Bir ortam seçip
kargonuzu kendi kelimelerinizle yazarsınız (pamuklu tişört, kablo, kauçuk conta, defter). Her eşya NASA'nın test ettiği
en yakın numuneye eşlenir ve tek cümlelik bir özet gösterilir; her sonuç, dayandığı NASA rapor sayfasına bağlanır.
Veri yoksa "veri yok" denir; tahmin yapılmaz ve hiçbir malzeme "güvenli" diye gösterilmez. Uygulama Türkçe ve İngilizce
çalışır, internetsiz ve API anahtarsız kullanılabilir.

*Team BeatlessFlame · NASA Space Apps 2026 · Ankara*
