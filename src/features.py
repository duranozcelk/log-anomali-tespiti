# =====================================================================
# features.py  —  ADIM 2: ÖZNİTELİK ÇIKARIMI (FEATURE ENGINEERING)
# ---------------------------------------------------------------------
# GÖREV : Temiz log tablosundaki istekleri IP adresine ve zaman
#         penceresine (1 dk ve 5 dk) göre gruplayıp, her grubun
#         davranışını 6 sayıyla (öznitelikle) özetlemek.
#
#   GİRDİ : data/temiz_log.csv          (3. haftanın çıktısı, her satır = 1 istek)
#   ÇIKTI : data/oznitelikler_1dk.csv   (her satır = 1 IP'nin 1 dakikalık davranışı)
#           data/oznitelikler_5dk.csv   (her satır = 1 IP'nin 5 dakikalık davranışı)
#
# NOT : Bu dosya etiketleri (etiketler.csv) KULLANMAZ. Hangi IP'nin
#       saldırgan olduğunu bilmeden, sadece davranışı sayıya döker.
#
# ÇALIŞTIRMA : python src/features.py
# =====================================================================

import os

import pandas as pd


# =====================================================================
# 1) AYARLAR
# =====================================================================

BU_DOSYA      = os.path.abspath(__file__)        # ...\log-anomali-tespiti\src\features.py
SRC_KLASORU   = os.path.dirname(BU_DOSYA)        # ...\log-anomali-tespiti\src
PROJE_KLASORU = os.path.dirname(SRC_KLASORU)     # ...\log-anomali-tespiti
DATA_KLASORU  = os.path.join(PROJE_KLASORU, "data")
TEMIZ_TABLO   = os.path.join(DATA_KLASORU, "temiz_log.csv")

# Hangi pencere sürelerinde hesap yapılacak (dakika)
#   1 dk -> ani istek patlamalarını yakalar
#   5 dk -> daha yavaş, uzun süren davranışları yakalar
PENCERELER = [1, 5]

# Raporundaki Tablo 2'nin 6 özniteliği (modele bu 6 sayı verilecek)
OZNITELIKLER = [
    "istek_sayisi",          # Penceredeki toplam istek sayısı
    "hata_orani",            # (404 + 403 sayısı) / toplam istek
    "saniyede_farkli_url",   # Farklı URL sayısı / pencere süresi (saniye)
    "giris_denemesi",        # Giriş sayfasına yapılan POST sayısı
    "toplam_mb",             # İndirilen toplam veri (MB)
    "gece_orani",            # 00:00-06:00 arası istek / toplam istek
]


# =====================================================================
# 2) ÖZNİTELİKLERİ HESAPLAYAN FONKSİYON
# =====================================================================

def oznitelikleri_hesapla(tablo, pencere_dk):
    """Temiz log tablosunu alır, her (IP + zaman penceresi) için 6 öznitelik hesaplar.

    tablo      : parser.py'nin ürettiği tablo (ip, zaman, metot, url, durum, boyut, ua)
    pencere_dk : pencere süresi (dakika), ör. 1 veya 5
    Döndürür   : her satırı bir IP'nin bir penceredeki davranışı olan yeni tablo
    """
    pencere_sn = pencere_dk * 60          # 5 dk -> 300 saniye
    tablo = tablo.copy()                  # Orijinal tabloyu bozmamak için kopyası üzerinde çalış

    # ---------------------------------------------------------------
    # Adım 1: Her isteğe "evet/hayır" işaretleri ekle (1 = evet, 0 = hayır)
    # Sonra bu işaretleri toplayınca "kaç tane?" sorusunun cevabı çıkar.
    # ---------------------------------------------------------------

    # Hata mı? -> durum kodu 403 (yasak) veya 404 (bulunamadı) ise 1
    tablo["hata_mi"] = tablo["durum"].isin([403, 404]).astype(int)

    # Giriş denemesi mi? -> metot POST VE adreste "login" geçiyorsa 1
    #   (/login, /wp-login.php, /admin/login gibi giriş sayfalarının hepsini yakalar)
    post_mu  = tablo["metot"] == "POST"
    login_mu = tablo["url"].str.contains("login")
    tablo["giris_mi"] = (post_mu & login_mu).astype(int)

    # Gece mi? -> saat 0, 1, 2, 3, 4 veya 5 ise (yani 06:00'dan önce) 1
    tablo["gece_mi"] = (tablo["zaman"].dt.hour < 6).astype(int)

    # ---------------------------------------------------------------
    # Adım 2: IP'ye ve zaman penceresine göre grupla
    # pd.Grouper(key="zaman", freq="5min") zamanı 5 dakikalık dilimlere böler.
    #   Örnek: 02:17:43 -> 02:15:00 penceresine (02:15-02:20) düşer.
    # Sonuç: aynı IP'nin aynı penceredeki bütün istekleri bir grup olur.
    # ---------------------------------------------------------------
    gruplar = tablo.groupby(["ip", pd.Grouper(key="zaman", freq=f"{pencere_dk}min")])

    # ---------------------------------------------------------------
    # Adım 3: Her grup için sayıları hesapla
    #   yeni_sutun_adi = (hangi sütundan, hangi işlemle)
    #   count   -> kaç satır var        sum -> toplamı
    #   nunique -> kaç FARKLI değer var
    # ---------------------------------------------------------------
    ozet = gruplar.agg(
        istek_sayisi   = ("url", "count"),       # kaç istek var
        hata_sayisi    = ("hata_mi", "sum"),     # kaç tanesi 403/404
        farkli_url     = ("url", "nunique"),     # kaç farklı URL istenmiş
        giris_denemesi = ("giris_mi", "sum"),    # kaç tanesi giriş denemesi
        toplam_bayt    = ("boyut", "sum"),       # toplam kaç bayt indirilmiş
        gece_istek     = ("gece_mi", "sum"),     # kaç tanesi gece
    )

    # Gruplama sonrası ip ve zaman "satır adı" olur; tekrar sıradan sütuna çevir
    ozet = ozet.reset_index()
    ozet = ozet.rename(columns={"zaman": "pencere"})    # "zaman" artık pencerenin başlangıcı

    # ---------------------------------------------------------------
    # Adım 4: Sayılardan oranları hesapla
    # ---------------------------------------------------------------
    ozet["hata_orani"]          = ozet["hata_sayisi"] / ozet["istek_sayisi"]
    ozet["saniyede_farkli_url"] = ozet["farkli_url"] / pencere_sn
    ozet["toplam_mb"]           = ozet["toplam_bayt"] / (1024 * 1024)      # bayt -> MB
    ozet["gece_orani"]          = ozet["gece_istek"] / ozet["istek_sayisi"]

    # ---------------------------------------------------------------
    # Adım 5: Sadece gerekli sütunları, sırasıyla al
    #   ip + pencere (kimlik bilgisi) + 6 öznitelik (modele gidecek sayılar)
    # ---------------------------------------------------------------
    sonuc = ozet[["ip", "pencere"] + OZNITELIKLER].copy()

    # Sayıları 4 ondalık basamağa yuvarla (0.946666... -> 0.9467), okunması kolay olsun
    sonuc[OZNITELIKLER] = sonuc[OZNITELIKLER].round(4)
    return sonuc


# =====================================================================
# 3) ANA PROGRAM
# =====================================================================

def main():
    if not os.path.exists(TEMIZ_TABLO):
        print("HATA: temiz_log.csv bulunamadı.")
        print("Önce şunu çalıştır: python src/parser.py")
        return

    # Temiz tabloyu oku. parse_dates: "zaman" sütununu tekrar tarih-saat türünde oku
    tablo = pd.read_csv(TEMIZ_TABLO, parse_dates=["zaman"])
    print(f"Okundu: {len(tablo)} istek, {tablo['ip'].nunique()} farklı IP")

    # Her pencere süresi için ayrı ayrı hesapla ve kaydet
    for pencere_dk in PENCERELER:
        oznitelikler = oznitelikleri_hesapla(tablo, pencere_dk)

        cikti_dosyasi = os.path.join(DATA_KLASORU, f"oznitelikler_{pencere_dk}dk.csv")
        oznitelikler.to_csv(cikti_dosyasi, index=False)

        print()
        print("=" * 90)
        print(f"{pencere_dk} DAKİKALIK PENCERE")
        print("=" * 90)
        print(f"Satır sayısı (IP + pencere): {len(oznitelikler)}")
        print(f"Kaydedildi: {cikti_dosyasi}")

        # Etiket kullanmadan bile en uç davranışlar göze çarpar:
        print()
        print("İstek sayısı en yüksek 5 pencere:")
        en_yogun = oznitelikler.sort_values("istek_sayisi", ascending=False).head(5)
        print(en_yogun.to_string(index=False))

        print()
        print("İndirilen veri en yüksek 5 pencere:")
        en_buyuk = oznitelikler.sort_values("toplam_mb", ascending=False).head(5)
        print(en_buyuk.to_string(index=False))


if __name__ == "__main__":
    main()
