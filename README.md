# Log Anomali Tespiti

**Sunucu Erişim Loglarında Makine Öğrenmesi Tabanlı Anomali ve İç Tehdit Tespiti**

Araştırma ve Yöntem Teknikleri dersi dönem projesi.

Bu proje, Nginx/Apache erişim loglarını otomatik olarak ayrıştırıp her IP adresinin
davranışını sayısal özniteliklere dönüştüren **hibrit** bir saldırı tespit sistemidir (IDS).
Açık saldırılar (SQL Injection, XSS) **kural tabanlı** olarak, sinsi davranış sapmaları
(brute-force, dizin tarama, anormal veri çekme) ise **Isolation Forest** ile tespit edilir.

> Bu sistem bir **alarm** sistemidir (IDS): şüpheli IP'leri raporlar, ancak engellemez.

---

## Sistem akışı

```
Ham Log  ->  Adım 1        ->  Adım 2            ->  Adım 3                   ->  Adım 4
access.log   Ayrıştırma        Öznitelik Çıkarımı    Hibrit Tespit               Doğrulama
(düz metin)  (Regex -> tablo)  (1 ve 5 dk pencere)   (Kural + Isolation Forest)  (Precision/Recall/F1)
```

## Klasör yapısı

```
log-anomali-tespiti/
├── data/        Log dosyaları ve etiketler (üretilen veri)
├── tools/       Yardımcı veri üretici betikler
├── src/         Asıl sistem modülleri (parser, features, rules, detector, evaluate)
├── notebooks/   Keşif/deneme defterleri
├── reports/     Çıktı raporları ve grafikler
├── requirements.txt
└── README.md
```

## Kurulum

```bash
# 1) Sanal ortam oluştur
python -m venv venv

# 2) Etkinleştir
#   Windows:  venv\Scripts\activate
#   Mac/Linux: source venv/bin/activate

# 3) Kütüphaneleri kur
pip install -r requirements.txt
```

## Çalıştırma

Komutlar proje ana klasöründen, sanal ortam etkinken **bu sırayla** çalıştırılmalıdır
(her adım bir öncekinin çıktısını kullanır):

```bash
# 1) Normal (saldırısız) örnek trafik üret       -> data/normal_trafik.log
python tools/normal_trafik_uret.py

# 2) Saldırıları ekle, test logu ve etiketleri üret -> data/test.log, data/etiketler.csv
python tools/saldiri_uret.py

# 3) Logu ayrıştır (Regex -> tablo)              -> data/temiz_log.csv, data/bozuk_satirlar.log,
#                                                   reports/ayristirma_ozeti.txt
python src/parser.py

# 4) Öznitelikleri çıkar (1 ve 5 dk pencere)     -> data/oznitelikler_1dk.csv, data/oznitelikler_5dk.csv
python src/features.py

# 5) Kural tabanlı SQLi/XSS filtresi             -> data/kural_eslesmeleri.csv,
#                                                   reports/kural_eslesme_raporu.csv
python src/rules.py
```

### Testler ve analiz

```bash
# Parser testi (5 sağlam + 4 bozuk satır)
python tools/parser_testi.py

# Kural testi (12 zararlı + 6 masum URL)
python tools/kural_testi.py

# Öznitelik dağılım grafikleri ve özet tabloları -> reports/oznitelik_dagilimi_*.png,
#                                                   reports/oznitelik_ozeti_*.csv
python tools/oznitelik_grafikleri.py
```

## Çalışma planı (8 hafta)

| Hafta | İş | Durum |
|------|-----|:-----:|
| 1 | Ortam kurulumu, klasör yapısı, Git, normal trafik üretimi | ✅ |
| 2 | Saldırı üretici betik + test logu + gerçek etiketler | ✅  |
| 3 | `parser.py` — Regex ile log ayrıştırma | ✅ |
| 4 | `features.py` — öznitelik çıkarımı | ✅ |
| 5 | `rules.py` — SQLi/XSS kural filtresi | ✅ |
| 6 | `detector.py` — Isolation Forest + uyarı raporu | ⬜ |
| 7 | `evaluate.py` — Precision/Recall/F1, karşılaştırmalar | ⬜ |
| 8 | Final raporu, sunum ve demo | ⬜ |

## Hedefler

- F1-Skoru ≥ 0,80
- False Positive oranı ≤ %2

## Kullanılan araçlar

Python 3 · Pandas · scikit-learn · Matplotlib · Regex · Git
