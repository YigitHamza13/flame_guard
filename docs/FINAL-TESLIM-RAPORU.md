# FINAL teslim kontrolü

Çalışma kaynağı: masaüstündeki FINAL..zip. Önceki FINAL-offline sürümü temel alınmadı.

## Tamamlananlar
- G1: Sekiz demo sorusu, TR/EN konu yanıtları, sınırlı yazım toleransı, yanlış Ay/kablo eşleşmesi regresyonları. Arayüz ve değerlendirme aynı çevrimdışı yanıt yolunu kullanır. Yerel PDF SHA-256 ve sayfa sınırı denetlenir. Eski işlevler/testler korunmuştur; tarihsel şablon API'si doğrudan kullanıcıya gösterilmez.
- G2: 38 soruluk yerel değerlendirme; 22/22 kaynak eşleşmesi, 12/12 kanıt yokken yanıt vermeme, 38/38 yanıt türü. Sonuçlar betikten üretilir ve kod/fixture değişirse arayüz eski sonucu göstermez. Bağımsız bilimsel doğrulama değildir.
- G3: Model boyutu görünen açık yükleme düğmesi, ilk açılışta GLB/kitaplık yüklememe, hata/yeniden deneme ve ilerleme. Slow 3G deneyi docs/PERFORMANCE.md içinde.
- Tema: ISS/Ay/Mars/Dünya taban renkleri, mevcut dokular, kaynaklı varsayımlardan ortam şeridi, reduced-motion desteği, kart renklerini değiştirmeyen vurgular, yerçekimi rozetleri, asistan soru önceliği. PDF rapor beyaz kalır. Dekoratif emoji kaldırıldı.
- G4: İzinli dosya listesiyle ZIP; asistan verileri, değerlendirme fixture'ı, betikler ve yerel görüntüleyici dahil. .env, secrets.toml, SQLite çalışma durumu ve loglar hariç.

## ATLANDI / açık sınırlar
- Saffire VI 20240002981 (alarm 981 sn) ve BASS-II 20210011385 (2,2–5 cm/sn) PDF'leri pakette yok. Yeni yanıtlarda bu sayılar kullanılmadı; dosya indirilmedi. Eski veri kartlarının tümü yeniden bilimsel incelemeden geçirilmedi. NASA onayı/uçuş yeterliliği iddia edilmez.
- Belgedeki test komutu `python -m pytest tests -q -p no:cacheprovider`: pytest kurulu değil. Yeni paket indirmeme kuralına uyuldu. Aynı test koleksiyonu unittest discovery ile çalıştırıldı; test silinmedi/atlatılmadı/gevşetilmedi. Geliştirici bağımlılıkları requirements-dev.txt içinde.
- Slow 3G altında büyük model 30 saniyelik gözlem penceresinde tamamlanmadı; tamamlanma süresi uydurulmadı. Normal yerel bağlantıda model yüklendi. Draco paketi kurulmadı.
- Sunulan asistan kaynak kontrollü yerel kurallardır; genel amaçlı yerel büyük dil modeli değildir. Ücretli API zorunlu değildir.

## Doğrulama
- Son unittest sonucu: 121 test; tümü başarılı (final-tests.log, teslim ZIP'ine log eklenmez).
- Playwright: 4 ortam × 8 sayfa × 2 genişlik (1440/390 px), 64 ekran; hata/yatay taşma kontrolü. Ekranlar çalışma kopyasının docs/theme_screens klasöründe; ZIP'i şişirmemek için görüntüler ZIP dışında tutulur.
- Tema metin/zemin, ikincil metin/yüzey ve vurgu/yüzey kontrastı ≥4,5:1 birim testleri. Gerçek açıklama opaklığı 1 olarak düzeltildi.

## Değişen ana dosyalar
app.py; src/answers.py, assistant_eval.py, theme.py, ui.py, pages.py, worlds.py, plain.py, access.py, ntrs.py, report.py; locales/en.json, tr.json; assets/context-model.html; static/js/model-viewer.min.js; data/assistant_sources.json, assistant_eval_result.json; tests/test_verified_assistant.py, test_assistant_eval.py, test_theme.py, test_model_loading.py, fixtures/assistant_eval.json; scripts/eval_assistant.py, measure_performance.cjs, verify_theme_browser.cjs, package_release.py; requirements-dev.txt; docs/PERFORMANCE.md.
