> Historical measurements for the previous click-to-load version. The deployment-ready version automatically starts the selected model; timings below are not a benchmark of this release.

# Yerel performans kontrolü

2026-11-15, Playwright + kurulu Chrome, 1440×1000, CDP Network.emulateNetworkConditions.
Profil: 400 ms gecikme, 50.000 bayt/sn indirme/yükleme, soğuk tarayıcı önbelleği. Tek ölçüm; istatistiksel performans garantisi değildir.

| Ölçüm | Önce | Sonra |
|---|---:|---:|
| İlk anlamlı içerik (ana sayfa başlığı görünür) | 105.724 sn | 69.032 sn |
| Kullanıcı tıklamasından önce GLB isteği | 1 | 0 |

3D model, 30 saniyelik gözlem penceresinde Slow 3G profilinde tamamlanmadı. Son durumda bu süre görüntüleyici kitaplığı indirmesini de kapsar; model tamamlanma süresi ölçülemedi. Normal yerel bağlantıda düğmeden sonra ISS modelinin loaded durumu doğrulandı. Eski 8 saniyelik otomatik vazgeçme kaldırıldı.

## Yerel modeller

| Dosya | Bayt | MB (ondalık) |
|---|---:|---:|
| earth.glb | 12916400 | 12.92 |
| iss.glb | 44495916 | 44.50 |
| mars.glb | 4032148 | 4.03 |
| moon.glb | 13799876 | 13.80 |

Modeller ve görüntüleyici kitaplığı yalnızca düğmeden sonra yüklenir. İlk görünüm mevcut yerel görseldir. Model yüklemesi sırasında ilerleme ve hatada tekrar deneme bulunur.

Draco/meshopt optimizasyonu önerisi: geometri/doku kalitesini ve gerekli çözücülerin çevrimdışı kullanılabilirliğini kontrol ederek ayrı bir optimizasyon turu yapılabilir. Paket kurulmadı, model dosyaları değiştirilmedi.

Tekrar: PLAYWRIGHT_MODULE ve CHROME_PATH değerlerini mevcut kurulumunuza ayarlayıp `node scripts/measure_performance.cjs after` çalıştırın (localhost:8765). Ham çıktılar docs/performance-*.json içinde. İlk başarısız seçici denemesi sonuçlara dahil edilmedi.
