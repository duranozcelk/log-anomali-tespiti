#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
saldiri_uret.py
---------------
normal_trafik.log dosyasini okur, icine KONTROLLU saldiri senaryolari ekler ve
ikisini birlestirip zamana gore sirali bir TEST logu uretir. Ayrica hangi IP'nin
hangi saldiriyi yaptigini "gercek etiket" (ground truth) olarak kaydeder.

Ciktilar:
    data/test.log        -> normal + saldiri (karisik, zamana gore sirali)
    data/etiketler.csv   -> saldirgan IP'ler ve saldiri turu (dogrulama icin)

NOT: Bu betik gercek bir saldiri YAPMAZ. Yalnizca saldirilarin bir log dosyasinda
     nasil gorundugunu taklit eden METIN satirlari uretir. Amac, tespit sistemini
     test edebilmek icin "cevap anahtari" olan yapay bir veri hazirlamaktir.

Calistirma (proje ana klasorunden, once normal_trafik_uret.py calistirilmali):
    python tools/saldiri_uret.py
"""

import os
import csv
import random
import datetime

SEED = 7
TARIH = datetime.date(2026, 3, 14)
TZ_OFFSET = datetime.timezone(datetime.timedelta(hours=3))   # +0300
TZ_STR = "+0300"
PROJE_KOKU = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI_KLASORU = os.path.join(PROJE_KOKU, "data")
NORMAL_LOG = os.path.join(VERI_KLASORU, "normal_trafik.log")
TEST_LOG = os.path.join(VERI_KLASORU, "test.log")
ETIKET_DOSYASI = os.path.join(VERI_KLASORU, "etiketler.csv")

random.seed(SEED)

# Saldirilarda sik gorulen otomatik arac imzalari (User-Agent)
ARAC_UA = [
    "python-requests/2.31.0",
    "curl/8.4.0",
    "Mozilla/5.0 (compatible; Nmap Scripting Engine)",
    "Go-http-client/1.1",
]

# Dizin taramasinda denenen tipik gizli/yedek yollar
DIZIN_LISTESI = [
    "/admin", "/admin/", "/administrator", "/admin/config.php", "/admin/login",
    "/wp-admin", "/wp-login.php", "/phpmyadmin", "/.env", "/.git/config",
    "/backup.zip", "/backup.tar.gz", "/db.sql", "/config.php.bak", "/old",
    "/test", "/dev", "/.htaccess", "/server-status", "/cgi-bin/", "/shell.php",
    "/uploads/", "/tmp/", "/private/", "/secret/", "/api/v1/users", "/.aws/credentials",
]


def zaman_metni(zaman):
    return zaman.strftime("%d/%b/%Y:%H:%M:%S") + " " + TZ_STR


def satir(ip, zaman, metot, url, durum, boyut, ua):
    return f'{ip} - - [{zaman_metni(zaman)}] "{metot} {url} HTTP/1.1" {durum} {boyut} "-" "{ua}"'


# --------------------------- SALDIRI SENARYOLARI ---------------------------

def brute_force(ip):
    """Tek IP, gece /login sayfasina ~5 dk icinde yuzlerce basarisiz giris."""
    satirlar = []
    ua = random.choice(ARAC_UA)
    t = datetime.datetime.combine(TARIH, datetime.time(2, 15, 0), tzinfo=TZ_OFFSET)
    for _ in range(500):
        durum = 401 if random.random() < 0.98 else 200   # cok nadir dogru sifre
        satirlar.append((t, satir(ip, t, "POST", "/login", durum,
                                  random.randint(200, 500), ua)))
        t = t + datetime.timedelta(milliseconds=random.randint(200, 900))
    return satirlar


def dizin_tarama(ip):
    """Tek IP, ~3 dk icinde binlerce farkli/var olmayan yolu dener (cogu 404)."""
    satirlar = []
    ua = "python-requests/2.31.0"
    t = datetime.datetime.combine(TARIH, datetime.time(4, 5, 0), tzinfo=TZ_OFFSET)
    for i in range(2000):
        if i < len(DIZIN_LISTESI):
            url = DIZIN_LISTESI[i]
        else:
            kok = random.choice(["admin", "backup", "old", "data", "files", "api"])
            url = f"/{kok}/{random.randint(1, 99999)}.php"
        durum = 404 if random.random() < 0.95 else 200
        satirlar.append((t, satir(ip, t, "GET", url, durum,
                                  random.randint(150, 500), ua)))
        t = t + datetime.timedelta(milliseconds=random.randint(50, 150))
    return satirlar


def gece_veri_cekme(ip):
    """Tek IP, gece 03:00-03:30 arasi toplam ~900 MB veri indirir (hepsi 200)."""
    satirlar = []
    ua = "curl/8.4.0"
    t = datetime.datetime.combine(TARIH, datetime.time(3, 0, 0), tzinfo=TZ_OFFSET)
    bitis = datetime.datetime.combine(TARIH, datetime.time(3, 30, 0), tzinfo=TZ_OFFSET)
    hedef = 900 * 1024 * 1024            # 900 MB (bayt)
    toplam = 0
    dosyalar = ["/export/veritabani_yedek.sql", "/downloads/musteri_listesi.csv",
                "/backup/full_backup.tar.gz", "/export/loglar.zip"]
    while toplam < hedef and t < bitis:
        boyut = random.randint(5 * 1024 * 1024, 30 * 1024 * 1024)   # 5-30 MB
        toplam += boyut
        satirlar.append((t, satir(ip, t, "GET", random.choice(dosyalar),
                                  200, boyut, ua)))
        t = t + datetime.timedelta(seconds=random.randint(1, 8))
    return satirlar


def enjeksiyon(ip):
    """Tek IP, URL'sine zararli SQLi/XSS kalibi gomulmus istekler atar.
    Bir kismi %27, %20 gibi URL-kodlu halde (unquote testi icin)."""
    satirlar = []
    ua = random.choice(ARAC_UA)
    # NOT: URL'lerde bosluk yok (log ayristirici boslukla boler); bosluklar
    # ya %20 ile kodlanmis ya da / ile degistirilmistir -> gercek evazyon teknikleri.
    kaliplar = [
        "/urun.php?id=5%27%20OR%201=1--",                                   # ' OR 1=1
        "/urun.php?id=5%27%20OR%20%271%27=%271",                            # ' OR '1'='1
        "/login?user=admin%27--",                                          # admin'--
        "/ara?q=1%20UNION%20SELECT%20username,password%20FROM%20users",    # UNION SELECT
        "/urun.php?id=1%3B%20DROP%20TABLE%20users--",                       # DROP TABLE
        "/ara?q=<script>alert(1)</script>",                                # <script>
        "/ara?q=%3Cscript%3Ealert(1)%3C/script%3E",                        # kodlu <script>
        "/profil?ad=<img/src=x/onerror=alert(1)>",                         # onerror=
        "/sayfa?url=javascript:alert(document.cookie)",                    # javascript:
        "/yorum?msg=%3Csvg/onload=alert(1)%3E",                            # kodlu onload
    ]
    t = datetime.datetime.combine(TARIH, datetime.time(15, 40, 0), tzinfo=TZ_OFFSET)
    for _ in range(50):
        durum = random.choice([200, 403, 500])
        satirlar.append((t, satir(ip, t, "GET", random.choice(kaliplar),
                                  durum, random.randint(200, 1500), ua)))
        t = t + datetime.timedelta(seconds=random.randint(3, 20))
    return satirlar


# ------------------------------- BIRLESTIRME -------------------------------

def normal_logu_oku():
    if not os.path.exists(NORMAL_LOG):
        raise FileNotFoundError(
            f"{NORMAL_LOG} bulunamadi. Once calistir: python tools/normal_trafik_uret.py"
        )
    with open(NORMAL_LOG, encoding="utf-8") as f:
        return [s.rstrip("\n") for s in f if s.strip()]


def zaman_coz(satir_metni):
    """Siralama icin bir log satirindan koseli parantez icindeki zamani ayiklar."""
    ic = satir_metni.split("[", 1)[1].split("]", 1)[0]       # 14/Mar/2026:03:12:07 +0300
    return datetime.datetime.strptime(ic, "%d/%b/%Y:%H:%M:%S %z")


def main():
    os.makedirs(VERI_KLASORU, exist_ok=True)

    # Saldirgan IP'ler sabit secildi -> etiket dosyasi net olsun
    saldirilar = [
        ("185.220.101.45", "brute_force",     brute_force),
        ("45.142.212.10",  "dizin_tarama",    dizin_tarama),
        ("91.134.20.7",    "gece_veri_cekme", gece_veri_cekme),
        ("193.34.76.22",   "sqli_xss",        enjeksiyon),
    ]

    birlesik = [(zaman_coz(s), s) for s in normal_logu_oku()]

    etiketler = []
    for ip, tur, fonk in saldirilar:
        uretilen = fonk(ip)
        birlesik.extend(uretilen)
        etiketler.append((ip, tur, len(uretilen)))

    birlesik.sort(key=lambda x: x[0])        # hepsini zamana gore sirala

    with open(TEST_LOG, "w", encoding="utf-8") as f:
        for _t, s in birlesik:
            f.write(s + "\n")

    with open(ETIKET_DOSYASI, "w", newline="", encoding="utf-8") as f:
        yaz = csv.writer(f)
        yaz.writerow(["ip", "etiket", "saldiri_turu", "uretilen_satir"])
        for ip, tur, adet in etiketler:
            yaz.writerow([ip, "saldiri", tur, adet])

    toplam = len(birlesik)
    saldiri_satir = sum(a for _, _, a in etiketler)
    print(f"[OK] test.log yazildi: {toplam} satir "
          f"({saldiri_satir} saldiri + {toplam - saldiri_satir} normal)")
    print(f"[OK] etiketler.csv yazildi: {len(etiketler)} saldirgan IP")
    for ip, tur, adet in etiketler:
        print(f"     - {ip:16s} {tur:16s} {adet} satir")


if __name__ == "__main__":
    main()
