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

```bash
# Normal (saldırısız) örnek trafik üret -> data/normal_trafik.log
python tools/normal_trafik_uret.py
```

## Çalışma planı (8 hafta)

| Hafta | İş | Durum |
|------|-----|:-----:|
| 1 | Ortam kurulumu, klasör yapısı, Git, normal trafik üretimi | ✅ Tamam |
| 2 | Saldırı üretici betik + test logu + gerçek etiketler | ⬜ |
| 3 | `parser.py` — Regex ile log ayrıştırma | ⬜ |
| 4 | `features.py` — öznitelik çıkarımı | ⬜ |
| 5 | `rules.py` — SQLi/XSS kural filtresi | ⬜ |
| 6 | `detector.py` — Isolation Forest + uyarı raporu | ⬜ |
| 7 | `evaluate.py` — Precision/Recall/F1, karşılaştırmalar | ⬜ |
| 8 | Final raporu, sunum ve demo | ⬜ |

## Hedefler

- F1-Skoru ≥ 0,80
- False Positive oranı ≤ %2

## Kullanılan araçlar

Python 3 · Pandas · scikit-learn · Matplotlib · Regex · Git
