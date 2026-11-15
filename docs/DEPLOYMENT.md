# FLAMEGUARD deploy paketi

Bu paket Python 3.12 / Streamlit uygulamasıdır. Statik HTML barındırma yerine Python veya Docker çalıştırabilen bir sunucu kullanın.

## 3D modeller

- ISS, Ay, Mars ve Dünya modeli ilgili görünüm açıldığında otomatik yüklenir.
- Kullanıcının model indirmesi veya yükleme düğmesine basması gerekmez.
- Yükleme sırasında yerel önizleme ve ilerleme yazısı görünür. Model hazır olduğunda önizlemenin yerini alır.
- Bağlantı/WebGL hatasında önizleme korunur ve tekrar deneme sunulur.
- GLB dosyaları `static/models/`, görüntüleyici `static/js/` içinde paketlidir. Harici CDN veya API anahtarı gerekmez.
- Tarayıcı modeli göstermek için dosyayı sunucudan otomatik aktarır; ilk açılış süresi bağlantıya bağlıdır. Yalnızca seçilen görünümün modeli yüklenir.

## Streamlit / Python sunucusu

ZIP içeriğini aynı dizin yapısıyla çıkarın. Python 3.12 kullanın:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

Streamlit Community Cloud'da depo giriş dosyası `app.py` ve Python sürümü 3.12 olmalıdır. `.streamlit/config.toml`, `static/`, `assets/`, `data/`, `sources/`, `locales/` ve `src/` klasörlerini depoya eksiksiz ekleyin. `server.enableStaticServing=true` ayarını koruyun. Ana dizine deploy edin; bu sürüm varlıkları `/app/static/` yolundan çağırır.

`data/` dizini uygulama kullanıcısına yazılabilir olmalıdır; SQLite ilk çalıştırmada oluşturulur. Kaynak verileri zaten pakettedir. Bir uygulama örneğiyle çalıştırın. Platform farklı bir port istiyorsa başlangıç komutundaki portu platformun verdiği değerle değiştirin.

## Docker

```sh
docker build -t flameguard .
docker run --rm -p 8501:8501 flameguard
```

Mevcut Dockerfile yerel statik dosyaları içerir, ayrı uygulama kullanıcısıyla çalışır ve sağlık kontrolü sunar. Reverse proxy WebSocket bağlantılarını desteklemelidir.

## Yayın sonrası kontrol

1. Yeni/gizli tarayıcı oturumunda ana sayfayı açın: ISS modeli tıklamadan görünmeli.
2. Ay, Mars ve Dünya ortamlarını seçin: ilgili model otomatik görünmeli.
3. Türkçe/İngilizce dilini ve döndürme kontrolünü deneyin.
4. `/app/static/js/model-viewer.min.js` ve dört `/app/static/models/*.glb` adresinin HTTP 200 verdiğini doğrulayın.
5. Sunucunun `/_stcore/health` kontrolünü doğrulayın.

## Doğrulama ve yeniden paketleme

Geliştirme araçları için `python -m pip install -r requirements-dev.txt` kullanın.

```sh
python -X utf8 -m unittest discover -s tests -v
python scripts/package_release.py
```

Paketleyici SHA-256 manifestini yeniden üretir; `.env`, sunucu sırları, SQLite çalışma dosyaları ve logları pakete eklemez. `docs/PERFORMANCE.md` önceki düğmeyle yükleme sürümünün tarihsel ölçümleridir; bu sürüm için performans garantisi değildir.
