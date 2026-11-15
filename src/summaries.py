"""Plain-language source summaries (EN/TR) shown with assistant excerpts; quotes stay in the original English."""
SUMMARIES = {
 "20150008962": [
  "The 27-test total is supported. The 24/3 ignition split needs reconciliation with additional non-ignitions of reused samples in the Appendix. Pressure is 1 atm for this study. SIBAL is 75% cotton and 25% fiberglass, about 0.32 mm thick.",
  "27 test toplamı destekleniyor. 24/3 ateşleme ayrımı, ekteki yeniden kullanılan numunelerin ek ateşlememe kayıtlarıyla uzlaştırılmalı. Çalışma basıncı 1 atm. SIBAL %75 pamuk, %25 cam elyafı ve yaklaşık 0,32 mm kalınlığında."
 ],
 "19960008389": [
  "WIF A–D used polyethylene insulation about 0.65 mm thick, at approximately 21% oxygen and 1 atm. WIF-C failed to propagate. WIF-D quenched after airflow stopped. These samples flew on USML-1.",
  "WIF A–D yaklaşık 0,65 mm polietilen yalıtım, %21 oksijen ve 1 atm koşullarını kullandı. WIF-C'de yayılım başarısız oldu. WIF-D akış durunca söndü. Numuneler USML-1'de test edildi."
 ],
 "20170008805": [
  "Silicone specimens 2-1 through 2-4 had a brief local gas flame without sustained burning or propagation. Their thicknesses were 0.27, 0.61, 1.03 and 0.37 mm. Initial oxygen was approximately 22.1%; airflow was 20 cm/s. Pressure is not established by the inspected sample table.",
  "Silikon 2-1 ile 2-4 numunelerinde kısa yerel gaz alevi görüldü, sürekli yanma veya yayılım oluşmadı. Kalınlıklar 0,27, 0,61, 1,03 ve 0,37 mm. Başlangıç oksijeni yaklaşık %22,1, akış 20 cm/s. İncelenen numune tablosu basıncı belirtmiyor."
 ],
 "SP-4225": [
  "The report includes four flat cellulose specimens with different thicknesses. Their ignition and burning are supported. Numerical oxygen, pressure, airflow and thickness values are absent from this section.",
  "Raporda farklı kalınlıklarda dört düz selüloz numunesi var. Ateşleme ve yanma bilgisi destekleniyor. Bu bölüm sayısal oksijen, basınç, akış ve kalınlık değerlerini belirtmiyor."
 ],
 "20250010653": [
  "LUCI flew SIBAL fabric and PMMA rods on a rotating sounding rocket to simulate lunar gravity. Reported spread: about 0.92 mm/s at the SIBAL flame base (p. 19) and about 1.5 mm/s at the PMMA flame tip (p. 21). Simulated gravity, not the lunar surface.",
  "LUCI, Ay yerçekimini benzetmek için SIBAL kumaşı ve PMMA çubukları dönen bir sonda roketinde uçurdu. Raporlanan yayılma: SIBAL alev tabanında yaklaşık 0,92 mm/s (s. 19), PMMA alev ucunda yaklaşık 1,5 mm/s (s. 21). Benzetilmiş yerçekimi; Ay yüzeyi değil."
 ],
 "20260001966": [
  "2026 NASA presentation on lunar and Martian gravity. SIBAL burning downward at lunar gravity: about 0.11 cm/s flame-base spread in a centrifuge drop test and about 0.086 cm/s on a parabolic flight (p. 22). No completed lunar-surface tests.",
  "Ay ve Mars yerçekimi üzerine 2026 NASA sunumu. Ay yerçekiminde aşağı yönde yanan SIBAL: santrifüjlü düşme testinde yaklaşık 0,11 cm/s, parabolik uçuşta yaklaşık 0,086 cm/s alev tabanı yayılması (s. 22). Tamamlanmış Ay yüzeyi testi yok."
 ],
 "20240015307": [
  "2024 poster on the planned FM² lunar-surface flammability test: SIBAL fabric and PMMA, with atmospheres of 21% O₂ at 14.7 psia and 34% O₂ at 8.2 psia (p. 1). Plan only, no lunar results yet.",
  "Planlanan FM² Ay yüzeyi yanıcılık testi üzerine 2024 posteri: SIBAL kumaş ve PMMA; 14,7 psia'da %21 O₂ ve 8,2 psia'da %34 O₂ atmosferleri (s. 1). Sadece plan; henüz Ay sonucu yok."
 ],
 "20250002114": [
  "2025 paper on solid-fuel ignition for lunar applications: short-duration lunar-gravity tests in a drop-tower centrifuge at 20.4 rpm (p. 7) plus a theory model. Limits appear only in plots, so no number is copied here.",
  "Ay uygulamaları için katı yakıt tutuşması üzerine 2025 makalesi: 20,4 rpm düşme kulesi santrifüjünde kısa süreli Ay yerçekimi testleri (s. 7) ve bir teori modeli. Sınırlar sadece grafikte olduğu için burada sayı aktarılmadı."
 ],
 "20210021318": [
  "2021 NASA overview of spacecraft fire-safety technology for exploration: capability gaps and a roadmap. Context only; dates are historical plans.",
  "Keşif görevleri için uzay aracı yangın güvenliği teknolojisine dair 2021 NASA özeti: yetenek boşlukları ve yol haritası. Sadece bağlam; tarihler geçmiş planlardır."
 ]
}


def summary_for(source_id, lang):
    pair = SUMMARIES.get(str(source_id))
    if not pair:
        return ''
    return pair[1] if lang == 'TR' else pair[0]


NOTES_TR = {
 "LUCI-SIBAL": "Benzetilmiş Ay yerçekimi; Ay yüzeyi değil. LUCI-PMMA ile aynı uçuş. 19. sayfa alev tabanı yayılmasını 0,92 mm/s verir; 33. sayfa bunu 0,9'a yuvarlar. Toplam test sayısı numune sayısından çıkarılmadı.",
 "LUCI-PMMA": "LUCI-SIBAL ile aynı uçuş. Alev ucu yayılması yaklaşık doğrusal; taban yayılması sabit değil. Oksijen yanma sırasında değişiyor; sabit bir sınır koşulu değil.",
 "ICES-WSTF": "WSTF'de ölçülmüş yüksek akışlı testler; sınırlar grafik piksellerinden aktarılmadı. Yöntem geliştirme aşamasında; kabul edilmiş bir Ay malzeme standardı değil.",
 "ICES-GRC": "GRC'de kısa süreli santrifüj testleri; yerçekimi gradyanı ve Coriolis etkileri var. Ay yüzeyi verisi değil. Beş malzeme beş test demek değil.",
 "ICES-MODEL": "Damköhler sayısı ve ısı aktarımı modeli. Model parametreleri ölçülmüş sonuç olarak aktarılmadı.",
 "FM2-PLAN-2024": "2024 tarihli plan: dört numune; 14,7 psia'da %21 O₂ ve 8,2 psia'da %34 O₂. Poster önceki laboratuvar çalışmalarını da içeriyor; tamamlanmış Ay yüzeyi testi bildirmiyor. Posterde CP-21 ve HLS tanımları birlikte geçiyor.",
 "FM2-PLAN-2026": "2024 planından ayrı, gözden geçirilmiş 2026 konsepti. 8,2 psia'da dört planlı atmosfer: %37/33/29/25 O₂. Tamamlanmış Ay yüzeyi test sonucu yok.",
 "LPSC-CENTRIFUGE": "Önceki deneysel çalışma 2026 sunumunda yeniden verilmiş; yeni test sayısı yok. Raporlanan çalışma koşulu 1 atm hava.",
 "LPSC-AIRCRAFT": "Test 2-29: 20 saniye boyunca aşağı yönde yayılma. Başlıkta Mars geçiyor ama burada ölçülmüş bir Mars satırı yok. Yeni toplam test sayısı yok.",
 "FIRE-SAFETY-CONTEXT": "2021 tarihli yetenek boşlukları ve yol haritası. Tarihler geçmiş planlardır, güncel görev takvimi değil.",
 "PMMA-2024-UNVERIFIED": "Makalenin tam PDF'i yok. Künye LPSC PDF'inin 20. sayfasında doğrulandı. Sayısal ölçüm aktarılmadı; inceleme için makale PDF'i gerekli."
}
