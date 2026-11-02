# =====================================================================
# saldiri_uret.py
# ---------------------------------------------------------------------
# GÖREV : Normal logun içine 4 tür sahte saldırı ekleyip test logu üretmek.
#
#   GİRDİ : data/normal_trafik.log  (önce normal_trafik_uret.py çalıştırılmalı)
#   ÇIKTI : data/test.log           (normal + saldırı, zaman sırasına göre karışık)
#           data/etiketler.csv      (hangi IP saldırgan -> CEVAP ANAHTARI)
#
# NOT : Gerçek bir saldırı YAPILMAZ. Sadece saldırıların logda nasıl
#       göründüğünü taklit eden METİN satırları yazılır.
#
# ÇALIŞTIRMA : python tools/saldiri_uret.py
# =====================================================================

import os
import random
from datetime import datetime, timedelta


# =====================================================================
# 1) AYARLAR
# =====================================================================

random.seed(7)     # Her çalıştırmada AYNI saldırılar üretilsin

# Dosya yolları (betik nereden çalıştırılırsa çalıştırılsın doğru yeri bulur)
BU_DOSYA       = os.path.abspath(__file__)        # ...\log-anomali-tespiti\tools\saldiri_uret.py
TOOLS_KLASORU  = os.path.dirname(BU_DOSYA)        # ...\log-anomali-tespiti\tools
PROJE_KLASORU  = os.path.dirname(TOOLS_KLASORU)   # ...\log-anomali-tespiti
DATA_KLASORU   = os.path.join(PROJE_KLASORU, "data")
NORMAL_LOG     = os.path.join(DATA_KLASORU, "normal_trafik.log")
TEST_LOG       = os.path.join(DATA_KLASORU, "test.log")
ETIKET_DOSYASI = os.path.join(DATA_KLASORU, "etiketler.csv")

# Saldırgan IP adresleri (cevap anahtarına bunlar yazılacak)
BRUTE_FORCE_IP  = "185.220.101.45"
DIZIN_TARAMA_IP = "45.142.212.10"
VERI_CEKME_IP   = "91.134.20.7"
ENJEKSIYON_IP   = "193.34.76.22"


# =====================================================================
# 2) YARDIMCI FONKSİYONLAR (normal_trafik_uret.py'deki ile aynı)
# =====================================================================

def log_satiri_yap(ip, zaman, metot, url, durum, boyut, tarayici):
    """Verilen bilgileri birleştirip tek bir log satırı (metin) oluşturur."""
    zaman_metni = zaman.strftime("%d/%b/%Y:%H:%M:%S")      # -> 14/Mar/2026:02:15:00
    return f'{ip} - - [{zaman_metni} +0300] "{metot} {url} HTTP/1.1" {durum} {boyut} "-" "{tarayici}"'


def satirdan_zaman_al(satir):
    """Bir log satırının içindeki zamanı bulur (sıralama için).
    '... [14/Mar/2026:02:15:00 +0300] ...'  ->  14/Mar/2026:02:15:00
    """
    sag_taraf = satir.split("[")[1]
    zaman_metni = sag_taraf.split(" ")[0]
    return datetime.strptime(zaman_metni, "%d/%b/%Y:%H:%M:%S")


# =====================================================================
# 3) SALDIRI 1 — BRUTE-FORCE (kaba kuvvet ile şifre deneme)
# =====================================================================

def brute_force_uret():
    """
    NE OLUYOR : Saldırgan /login sayfasına art arda yüzlerce şifre dener.

    ZAMANLAMA :
        Başlangıç     : 02:15:00
        İstek sayısı  : 500
        İstek arası   : 0,4 - 0,8 saniye   (ortalama 0,6 sn)
        Toplam süre   : 500 x 0,6 sn = 300 sn = 5 dakika   (02:15 -> 02:20)

    LOGDAKİ İZİ : Aynı IP, çok sayıda "POST /login", neredeyse hepsi 401 (yanlış şifre)
    """
    satirlar = []
    zaman = datetime(2026, 3, 14, 2, 15, 0)        # başlangıç: 14 Mart 2026, 02:15:00

    for i in range(500):
        # %98 yanlış şifre (401), %2 doğru şifre (200)
        if random.randint(1, 100) <= 98:
            durum = 401
        else:
            durum = 200

        satir = log_satiri_yap(BRUTE_FORCE_IP, zaman, "POST", "/login", durum, 350, "python-requests/2.31.0")
        satirlar.append(satir)

        # ZAMAN İLERLER: bir sonraki denemeye kadar 400-800 milisaniye geçer
        bekleme_ms = random.randint(400, 800)
        zaman = zaman + timedelta(milliseconds=bekleme_ms)

    return satirlar


# =====================================================================
# 4) SALDIRI 2 — DİZİN TARAMA (gizli dosya/klasör arama)
# =====================================================================

# Botların ilk denediği bilinen gizli yollar
GIZLI_YOLLAR = [
    "/admin", "/admin/config.php", "/wp-admin", "/phpmyadmin", "/.env",
    "/.git/config", "/backup.zip", "/db.sql", "/config.php.bak", "/server-status",
]

def dizin_tarama_uret():
    """
    NE OLUYOR : Bir bot, sitede gizli dosya var mı diye binlerce farklı yolu dener.

    ZAMANLAMA :
        Başlangıç     : 04:05:00
        İstek sayısı  : 2000
        İstek arası   : 60 - 120 milisaniye   (ortalama 0,09 sn)
        Toplam süre   : 2000 x 0,09 sn = 180 sn = 3 dakika   (04:05 -> 04:08)

    LOGDAKİ İZİ : Çok sayıda FARKLI URL, çoğu 404 (bulunamadı), insanüstü hız
    """
    satirlar = []
    zaman = datetime(2026, 3, 14, 4, 5, 0)          # başlangıç: 04:05:00

    for i in range(2000):
        # Önce bilinen gizli yolları dene; liste bitince uydurma yollar dene
        if i < len(GIZLI_YOLLAR):
            url = GIZLI_YOLLAR[i]
        else:
            url = "/dosya" + str(i) + ".php"        # /dosya10.php, /dosya11.php, ...

        # %95 bulunamadı (404), %5 bulundu (200)
        if random.randint(1, 100) <= 95:
            durum = 404
        else:
            durum = 200

        satir = log_satiri_yap(DIZIN_TARAMA_IP, zaman, "GET", url, durum, 300, "python-requests/2.31.0")
        satirlar.append(satir)

        # ZAMAN İLERLER: bir sonraki denemeye kadar 60-120 milisaniye geçer
        bekleme_ms = random.randint(60, 120)
        zaman = zaman + timedelta(milliseconds=bekleme_ms)

    return satirlar


# =====================================================================
# 5) SALDIRI 3 — GECE VERİ ÇEKME (anormal miktarda veri indirme)
# =====================================================================

def veri_cekme_uret():
    """
    NE OLUYOR : Biri gece saatlerinde sunucudan çok büyük miktarda veri indirir.

    ZAMANLAMA :
        Başlangıç     : 03:00:00
        İstek sayısı  : 60 dosya indirme
        İstek arası   : 20 - 30 saniye   (ortalama 25 sn)
        Toplam süre   : 60 x 25 sn = 1500 sn = 25 dakika   (03:00 -> ~03:25)

    VERİ MİKTARI : Her dosya 13-17 MB  ->  60 x 15 MB = yaklaşık 900 MB

    LOGDAKİ İZİ : Her istek BAŞARILI (200) görünür!
                  Şüpheli olan: gece saati + toplam veri miktarı.
    """
    satirlar = []
    zaman = datetime(2026, 3, 14, 3, 0, 0)          # başlangıç: 03:00:00

    for i in range(60):
        url = "/export/yedek_" + str(i) + ".zip"    # /export/yedek_0.zip, /export/yedek_1.zip, ...

        # Dosya boyutu: 13-17 MB arası. Logda bayt yazılır (1 MB = 1024 x 1024 bayt)
        boyut = random.randint(13, 17) * 1024 * 1024

        satir = log_satiri_yap(VERI_CEKME_IP, zaman, "GET", url, 200, boyut, "curl/8.4.0")
        satirlar.append(satir)

        # ZAMAN İLERLER: bir sonraki indirmeye kadar 20-30 saniye geçer
        bekleme = random.randint(20, 30)
        zaman = zaman + timedelta(seconds=bekleme)

    return satirlar


# =====================================================================
# 6) SALDIRI 4 — SQL INJECTION ve XSS (URL'ye zararlı kod gömme)
# =====================================================================

# URL'lerde boşluk olamaz, bu yüzden saldırganlar karakterleri KODLAR:
#   %20 = boşluk     %27 = ' (tek tırnak)     %3C = <     %3E = >
ZARARLI_URLLER = [
    "/urun.php?id=5%27%20OR%201=1--",               # çözülünce: 5' OR 1=1--             (SQL Injection)
    "/ara?q=1%20UNION%20SELECT%20kullanici,sifre",   # çözülünce: 1 UNION SELECT ...      (SQL Injection)
    "/urun.php?id=1;DROP%20TABLE%20kullanicilar",    # çözülünce: 1;DROP TABLE ...        (SQL Injection)
    "/ara?q=<script>alert(1)</script>",              # kodlanmamış                         (XSS)
    "/ara?q=%3Cscript%3Ealert(1)%3C/script%3E",      # çözülünce: <script>alert(1)</script> (XSS)
    "/profil?ad=<img/src=x/onerror=alert(1)>",       # kodlanmamış                         (XSS)
]

def enjeksiyon_uret():
    """
    NE OLUYOR : Saldırgan URL'nin içine zararlı SQL veya JavaScript kodu gömer.

    ZAMANLAMA :
        Başlangıç     : 15:40:00  (gündüz -> normal trafiğin arasına karışır)
        İstek sayısı  : 50
        İstek arası   : 5 - 15 saniye   (ortalama 10 sn)
        Toplam süre   : 50 x 10 sn = 500 sn = yaklaşık 8 dakika   (15:40 -> ~15:48)

    LOGDAKİ İZİ : URL'nin İÇERİĞİ (OR 1=1, UNION SELECT, <script> ...)
    """
    satirlar = []
    zaman = datetime(2026, 3, 14, 15, 40, 0)        # başlangıç: 15:40:00

    for i in range(50):
        url = random.choice(ZARARLI_URLLER)
        durum = random.choice([200, 403, 500])      # sunucu bazen cevap verir, bazen engeller, bazen çöker

        satir = log_satiri_yap(ENJEKSIYON_IP, zaman, "GET", url, durum, 800, "curl/8.4.0")
        satirlar.append(satir)

        # ZAMAN İLERLER: bir sonraki denemeye kadar 5-15 saniye geçer
        bekleme = random.randint(5, 15)
        zaman = zaman + timedelta(seconds=bekleme)

    return satirlar


# =====================================================================
# 7) ANA PROGRAM
# =====================================================================

def main():
    # --- Adım 1: Normal logu oku ---
    if not os.path.exists(NORMAL_LOG):
        print("HATA: normal_trafik.log bulunamadı.")
        print("Önce şunu çalıştır: python tools/normal_trafik_uret.py")
        return

    tum_satirlar = []
    with open(NORMAL_LOG, encoding="utf-8") as dosya:
        for satir in dosya:
            satir = satir.strip()          # satır sonundaki "\n" karakterini sil
            if satir != "":                # boş satırları atla
                tum_satirlar.append(satir)
    normal_sayisi = len(tum_satirlar)

    # --- Adım 2: 4 saldırıyı üret ---
    brute      = brute_force_uret()
    tarama     = dizin_tarama_uret()
    veri       = veri_cekme_uret()
    enjeksiyon = enjeksiyon_uret()

    # --- Adım 3: Saldırıları normal satırların listesine ekle ---
    tum_satirlar.extend(brute)
    tum_satirlar.extend(tarama)
    tum_satirlar.extend(veri)
    tum_satirlar.extend(enjeksiyon)

    # --- Adım 4: Hepsini zamana göre sırala ---
    # Böylece saldırılar normal trafiğin arasına karışır (gerçek bir sunucudaki gibi)
    tum_satirlar.sort(key=satirdan_zaman_al)

    # --- Adım 5: test.log dosyasını yaz ---
    with open(TEST_LOG, "w", encoding="utf-8") as dosya:
        for satir in tum_satirlar:
            dosya.write(satir + "\n")

    # --- Adım 6: Cevap anahtarını (etiketler.csv) yaz ---
    # Bu dosya MODELE VERİLMEZ. Sadece sonuçları puanlamak için kullanılır.
    with open(ETIKET_DOSYASI, "w", encoding="utf-8") as dosya:
        dosya.write("ip,saldiri_turu\n")
        dosya.write(BRUTE_FORCE_IP  + ",brute_force\n")
        dosya.write(DIZIN_TARAMA_IP + ",dizin_tarama\n")
        dosya.write(VERI_CEKME_IP   + ",gece_veri_cekme\n")
        dosya.write(ENJEKSIYON_IP   + ",sqli_xss\n")

    # --- Adım 7: Ekrana özet yaz ---
    print(f"Tamam: test.log yazıldı -> toplam {len(tum_satirlar)} satır")
    print(f"   Normal satır      : {normal_sayisi}")
    print(f"   Brute-force       : {len(brute)}")
    print(f"   Dizin tarama      : {len(tarama)}")
    print(f"   Gece veri çekme   : {len(veri)}")
    print(f"   SQLi / XSS        : {len(enjeksiyon)}")
    print("Tamam: etiketler.csv yazıldı (4 saldırgan IP)")


# Bu dosya doğrudan çalıştırılınca main() başlar
if __name__ == "__main__":
    main()
