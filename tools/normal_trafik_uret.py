# =====================================================================
# normal_trafik_uret.py
# ---------------------------------------------------------------------
# GÖREV : Normal kullanıcıların siteyi gezmesini taklit eden sahte bir
#         sunucu logu üretmek.
# ÇIKTI : data/normal_trafik.log
# ÇALIŞTIRMA : python tools/normal_trafik_uret.py
# =====================================================================

import os
import random
from datetime import datetime, timedelta


# =====================================================================
# 1) AYARLAR
# =====================================================================

random.seed(42)            # Her çalıştırmada AYNI log çıksın (tekrarlanabilirlik)
KULLANICI_SAYISI = 200     # Kaç farklı normal kullanıcı (IP) üretilecek

# Dosyanın kaydedileceği yeri buluyoruz: proje klasöründeki "data" klasörü.
# Böylece betik hangi klasörden çalıştırılırsa çalıştırılsın doğru yere yazar.
BU_DOSYA      = os.path.abspath(__file__)         # ...\log-anomali-tespiti\tools\normal_trafik_uret.py
TOOLS_KLASORU = os.path.dirname(BU_DOSYA)         # ...\log-anomali-tespiti\tools
PROJE_KLASORU = os.path.dirname(TOOLS_KLASORU)    # ...\log-anomali-tespiti
DATA_KLASORU  = os.path.join(PROJE_KLASORU, "data")
CIKTI_DOSYASI = os.path.join(DATA_KLASORU, "normal_trafik.log")

# Normal kullanıcıların gezdiği sayfalar
SAYFALAR = [
    "/", "/urunler", "/urun.php?id=12", "/urun.php?id=45", "/sepet",
    "/hakkimizda", "/iletisim", "/blog", "/hesabim", "/images/logo.png",
]

# Normal kullanıcıların tarayıcıları (User-Agent bilgisi)
TARAYICILAR = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Firefox/121.0",
]


# =====================================================================
# 2) YARDIMCI FONKSİYONLAR
# =====================================================================

def log_satiri_yap(ip, zaman, metot, url, durum, boyut, tarayici):
    """Verilen bilgileri birleştirip tek bir log satırı (metin) oluşturur.

    Örnek çıktı:
    85.12.40.7 - - [14/Mar/2026:10:15:32 +0300] "GET /sepet HTTP/1.1" 200 5120 "-" "Mozilla/5.0 ..."
    """
    zaman_metni = zaman.strftime("%d/%b/%Y:%H:%M:%S")      # -> 14/Mar/2026:10:15:32
    return f'{ip} - - [{zaman_metni} +0300] "{metot} {url} HTTP/1.1" {durum} {boyut} "-" "{tarayici}"'


def rastgele_ip():
    """85.12.40.7 gibi rastgele bir IP adresi üretir (4 sayı, aralarında nokta)."""
    a = random.randint(1, 223)
    b = random.randint(0, 255)
    c = random.randint(0, 255)
    d = random.randint(1, 254)
    return f"{a}.{b}.{c}.{d}"


def satirdan_zaman_al(satir):
    """Bir log satırının içindeki zamanı bulur. Satırları sıralamak için gerekli.

    satir   : '85.12.40.7 - - [14/Mar/2026:10:15:32 +0300] "GET / ...'
    1. adım : '[' işaretinden böl, sağ tarafı al  -> '14/Mar/2026:10:15:32 +0300] "GET / ...'
    2. adım : boşluktan böl, ilk parçayı al       -> '14/Mar/2026:10:15:32'
    3. adım : bu metni gerçek bir tarih-saate çevir
    """
    sag_taraf = satir.split("[")[1]
    zaman_metni = sag_taraf.split(" ")[0]
    return datetime.strptime(zaman_metni, "%d/%b/%Y:%H:%M:%S")


# =====================================================================
# 3) BİR KULLANICININ GÜNÜNÜ ÜRETEN FONKSİYON
# =====================================================================

def kullanici_uret():
    """Bir normal kullanıcının gün içindeki tüm isteklerini (log satırlarını) üretir."""
    ip = rastgele_ip()
    tarayici = random.choice(TARAYICILAR)
    satirlar = []

    oturum_sayisi = random.randint(1, 4)          # Kullanıcı siteye günde 1-4 kez girer
    for oturum in range(oturum_sayisi):

        # --- Oturumun BAŞLANGIÇ saati ---
        # Girişlerin %90'ı gündüz (08-22 arası), %10'u gece (00-07 arası) olur.
        if random.randint(1, 100) <= 90:
            saat = random.randint(8, 22)
        else:
            saat = random.randint(0, 7)
        dakika = random.randint(0, 59)
        saniye = random.randint(0, 59)
        zaman = datetime(2026, 3, 14, saat, dakika, saniye)     # 14 Mart 2026

        # --- Oturum boyunca gezilen sayfalar ---
        sayfa_sayisi = random.randint(3, 15)       # Her girişte 3-15 sayfa gezer
        for i in range(sayfa_sayisi):
            url = random.choice(SAYFALAR)

            # Sunucunun cevabı (durum kodu) ve gönderdiği veri miktarı (bayt)
            zar = random.randint(1, 100)
            if zar <= 90:              # %90 -> sayfa başarıyla geldi
                durum = 200
                boyut = random.randint(500, 50000)
            elif zar <= 97:            # %7  -> sayfa değişmemiş, tarayıcı kendi kopyasını kullandı
                durum = 304
                boyut = "-"            #        veri gönderilmedi -> logda "-" yazar
            else:                      # %3  -> kırık bağlantı, sayfa bulunamadı
                durum = 404
                boyut = random.randint(150, 600)

            satir = log_satiri_yap(ip, zaman, "GET", url, durum, boyut, tarayici)
            satirlar.append(satir)

            # ZAMAN İLERLER: Kullanıcı sayfayı okur, 5-20 saniye sonra diğer sayfaya geçer.
            bekleme = random.randint(5, 20)
            zaman = zaman + timedelta(seconds=bekleme)

    return satirlar


# =====================================================================
# 4) ANA PROGRAM
# =====================================================================

def main():
    tum_satirlar = []

    # 200 kullanıcıyı üret, hepsinin satırlarını tek listede topla
    for k in range(KULLANICI_SAYISI):
        kullanici_satirlari = kullanici_uret()
        tum_satirlar.extend(kullanici_satirlari)      # listenin sonuna ekle

    # Gerçek log dosyaları zaman sırasındadır.
    # sort'a "her satırın zamanına bakarak sırala" diyoruz.
    tum_satirlar.sort(key=satirdan_zaman_al)

    # Dosyaya yaz (data klasörü yoksa önce oluştur)
    os.makedirs(DATA_KLASORU, exist_ok=True)
    with open(CIKTI_DOSYASI, "w", encoding="utf-8") as dosya:   # with bitince dosya kendiliğinden kapanır
        for satir in tum_satirlar:
            dosya.write(satir + "\n")                           # "\n" = alt satıra geç

    print(f"Tamam: {len(tum_satirlar)} normal satır yazıldı -> {CIKTI_DOSYASI}")


# Bu dosya doğrudan çalıştırılınca main() başlar
if __name__ == "__main__":
    main()
