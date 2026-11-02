# =====================================================================
# oznitelik_grafikleri.py  —  KEŞİFSEL ANALİZ (4. hafta)
# ---------------------------------------------------------------------
# GÖREV : Normal ve saldırgan IP'lerin öznitelik değerlerini yan yana
#         çizip "hangi öznitelik hangi saldırıyı ele veriyor?" sorusunu
#         görsel olarak cevaplamak.
#
#   GİRDİ : data/oznitelikler_1dk.csv, data/oznitelikler_5dk.csv  (features.py çıktısı)
#           data/etiketler.csv                                    (cevap anahtarı)
#   ÇIKTI : reports/oznitelik_dagilimi_1dk.png, reports/oznitelik_dagilimi_5dk.png
#           reports/oznitelik_ozeti_1dk.csv,    reports/oznitelik_ozeti_5dk.csv
#
# NOT : Etiketler burada SADECE grafiği renklendirmek için kullanılır.
#       Modele giden features.py etiketleri hiç görmez.
#
# ÇALIŞTIRMA : python tools/oznitelik_grafikleri.py
# =====================================================================

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =====================================================================
# 1) AYARLAR
# =====================================================================

BU_DOSYA        = os.path.abspath(__file__)         # ...\log-anomali-tespiti\tools\oznitelik_grafikleri.py
TOOLS_KLASORU   = os.path.dirname(BU_DOSYA)         # ...\log-anomali-tespiti\tools
PROJE_KLASORU   = os.path.dirname(TOOLS_KLASORU)    # ...\log-anomali-tespiti
DATA_KLASORU    = os.path.join(PROJE_KLASORU, "data")
REPORTS_KLASORU = os.path.join(PROJE_KLASORU, "reports")
ETIKET_DOSYASI  = os.path.join(DATA_KLASORU, "etiketler.csv")

PENCERELER = [1, 5]

# Çizilecek 6 öznitelik ve grafikteki başlıkları
OZNITELIKLER = ["istek_sayisi", "hata_orani", "saniyede_farkli_url",
                "giris_denemesi", "toplam_mb", "gece_orani"]
BASLIKLAR = {
    "istek_sayisi":        "İstek sayısı",
    "hata_orani":          "Hata oranı (403+404)",
    "saniyede_farkli_url": "Saniyedeki farklı URL",
    "giris_denemesi":      "Giriş denemesi (POST login)",
    "toplam_mb":           "Toplam indirilen veri (MB)",
    "gece_orani":          "Gece isteği oranı",
}

# Grafikte soldan sağa gruplar ve renkleri
GRUPLAR = ["normal", "brute_force", "dizin_tarama", "gece_veri_cekme", "sqli_xss"]
GRUP_ADLARI = ["Normal", "Brute-force", "Dizin\ntarama", "Gece veri\nçekme", "SQLi/XSS"]
RENKLER = {
    "normal":          "gray",
    "brute_force":     "red",
    "dizin_tarama":    "orange",
    "gece_veri_cekme": "purple",
    "sqli_xss":        "blue",
}

np.random.seed(0)     # Noktaların yatay kaydırması her seferinde aynı olsun


# =====================================================================
# 2) TABLOYU OKUYUP GRUP BİLGİSİ EKLEYEN FONKSİYON
# =====================================================================

def tabloyu_hazirla(pencere_dk):
    """Öznitelik tablosunu okur ve her satıra 'grup' sütunu ekler
    (normal, brute_force, dizin_tarama, gece_veri_cekme, sqli_xss)."""
    dosya = os.path.join(DATA_KLASORU, f"oznitelikler_{pencere_dk}dk.csv")
    tablo = pd.read_csv(dosya)
    etiketler = pd.read_csv(ETIKET_DOSYASI)

    # IP -> saldırı türü sözlüğü:  {"185.220.101.45": "brute_force", ...}
    ip_tur_sozlugu = dict(zip(etiketler["ip"], etiketler["saldiri_turu"]))

    # Her satırın IP'sini sözlükte ara. Bulunamazsa (saldırgan değilse) "normal" yaz.
    tablo["grup"] = tablo["ip"].map(ip_tur_sozlugu).fillna("normal")
    return tablo


# =====================================================================
# 3) GRUPLARIN ORTANCA (MEDYAN) DEĞERLERİNİ ÇIKARAN FONKSİYON
# =====================================================================

def ozet_tablosu(tablo):
    """Her grubun her öznitelikteki ortanca (medyan) değerini verir.
    Ortanca: sayılar sıralanınca tam ortada kalan değer (uç değerlerden etkilenmez)."""
    ozet = tablo.groupby("grup")[OZNITELIKLER].median()
    ozet = ozet.reindex(GRUPLAR)                  # satırları bizim sıramıza diz
    ozet["pencere_sayisi"] = tablo["grup"].value_counts().reindex(GRUPLAR)
    return ozet.round(3)


# =====================================================================
# 4) GRAFİĞİ ÇİZEN FONKSİYON
# =====================================================================

def grafik_ciz(tablo, pencere_dk, kayit_yolu):
    """2 satır x 3 sütun = 6 küçük grafik. Her grafikte bir öznitelik,
    her noktada bir IP'nin bir penceresi var."""
    sekil, eksenler = plt.subplots(2, 3, figsize=(16, 9))
    eksenler = eksenler.flatten()          # 2x3 düzeni düz bir listeye çevir: [0..5]

    for i in range(len(OZNITELIKLER)):
        oznitelik = OZNITELIKLER[i]
        eksen = eksenler[i]

        for x in range(len(GRUPLAR)):
            grup = GRUPLAR[x]
            degerler = tablo[tablo["grup"] == grup][oznitelik]

            # Noktalar üst üste binmesin diye her noktayı yatayda biraz kaydır
            kaydirma = np.random.uniform(-0.25, 0.25, len(degerler))

            # Saldırgan noktaları az sayıda; gözden kaçmasınlar diye daha büyük çiz
            if grup == "normal":
                boyut = 12
            else:
                boyut = 50
            eksen.scatter(x + kaydirma, degerler, s=boyut, alpha=0.6, color=RENKLER[grup])

        eksen.set_title(BASLIKLAR[oznitelik], fontsize=12)
        eksen.set_xticks(range(len(GRUPLAR)))
        eksen.set_xticklabels(GRUP_ADLARI, fontsize=9)

        # Değerler 0 ile binler arasında değişiyor. Logaritmik eksen küçük ve
        # büyük değerleri aynı grafikte görünür kılar (0 değeri de gösterilebilir).
        eksen.set_yscale("symlog", linthresh=0.01)

        # Eksen sınırları: altta 0'ın biraz altı, üstte en büyük değerin 3 katı
        # (böylece uçtaki noktalar kenara yapışıp kesilmez)
        en_buyuk = tablo[oznitelik].max()
        eksen.set_ylim(-0.005, max(en_buyuk * 3, 1))
        eksen.grid(axis="y", alpha=0.3)

    sekil.suptitle(f"Öznitelik dağılımları ({pencere_dk} dakikalık pencere) - "
                   "her nokta bir IP'nin bir penceresi", fontsize=14)
    sekil.tight_layout()
    sekil.savefig(kayit_yolu, dpi=120)
    plt.close(sekil)


# =====================================================================
# 5) ANA PROGRAM
# =====================================================================

def main():
    os.makedirs(REPORTS_KLASORU, exist_ok=True)

    for pencere_dk in PENCERELER:
        dosya = os.path.join(DATA_KLASORU, f"oznitelikler_{pencere_dk}dk.csv")
        if not os.path.exists(dosya):
            print(f"HATA: {dosya} bulunamadı. Önce şunu çalıştır: python src/features.py")
            return

        tablo = tabloyu_hazirla(pencere_dk)

        # Ortanca değer tablosu
        ozet = ozet_tablosu(tablo)
        ozet_yolu = os.path.join(REPORTS_KLASORU, f"oznitelik_ozeti_{pencere_dk}dk.csv")
        ozet.to_csv(ozet_yolu)

        print("=" * 100)
        print(f"{pencere_dk} DAKİKALIK PENCERE - grupların ortanca (medyan) değerleri")
        print("=" * 100)
        print(ozet.to_string())
        print()

        # Grafik
        grafik_yolu = os.path.join(REPORTS_KLASORU, f"oznitelik_dagilimi_{pencere_dk}dk.png")
        grafik_ciz(tablo, pencere_dk, grafik_yolu)
        print(f"Kaydedildi: {ozet_yolu}")
        print(f"Kaydedildi: {grafik_yolu}")
        print()


if __name__ == "__main__":
    main()
