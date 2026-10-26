#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normal_trafik_uret.py
---------------------
Gercekci "normal" kullanici trafigi iceren bir Nginx/Apache erisim logu uretir.
Bicim: Combined Log Format (projede kullanilacak bicim).

Cikti: data/normal_trafik.log

Calistirma (proje ana klasorunden):
    python tools/normal_trafik_uret.py
"""

import os
import random
import datetime

# ------------------------------- AYARLAR -------------------------------
SEED = 42                        # Ayni sonucu tekrar uretebilmek icin sabit tohum
TARIH = datetime.date(2026, 3, 14)
TZ = "+0300"                     # Zaman dilimi (Turkiye)
CIKTI_DOSYASI = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "normal_trafik.log")
NORMAL_KULLANICI_SAYISI = 200    # Kac farkli normal kullanici (IP) olacak
# -----------------------------------------------------------------------

random.seed(SEED)

# Normal bir sitede gezilebilecek gercek sayfalar
NORMAL_SAYFALAR = [
    "/", "/index.html", "/urunler", "/urunler?kategori=elektronik",
    "/urunler?kategori=giyim", "/urun.php?id=12", "/urun.php?id=45",
    "/urun.php?id=103", "/hakkimizda", "/iletisim", "/blog",
    "/blog/kampanyalar", "/sepet", "/hesabim",
    "/static/css/style.css", "/static/js/app.js",
    "/images/logo.png", "/images/banner.jpg", "/favicon.ico",
]

# Gercek tarayicilarin User-Agent bilgileri
NORMAL_UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Saatlere gore yogunluk agirligi (0-23). Gunduz yuksek, gece dusuk.
SAAT_AGIRLIKLARI = [1, 1, 1, 1, 1, 2, 4, 8, 12, 14, 15, 15,
                    14, 13, 14, 15, 14, 12, 10, 8, 6, 4, 2, 1]


def rastgele_ip():
    """Gercekci gorunen rastgele bir IPv4 adresi uretir."""
    return (f"{random.randint(1, 223)}.{random.randint(0, 255)}."
            f"{random.randint(0, 255)}.{random.randint(1, 254)}")


def rastgele_zaman():
    """Gun icinde, gunduz saatlerine daha cok dusen rastgele bir zaman uretir."""
    saat = random.choices(range(24), weights=SAAT_AGIRLIKLARI)[0]
    return datetime.datetime.combine(
        TARIH, datetime.time(saat, random.randint(0, 59), random.randint(0, 59))
    )


def durum_ve_boyut(url):
    """Bir istek icin gercekci HTTP durum kodu ve yanit boyutu secer."""
    r = random.random()
    if r < 0.93:
        durum = 200
    elif r < 0.98:
        return 304, 0          # Onbellekten geldi (icerik degismedi)
    else:
        durum = 404            # Normal kullanici da bazen kirik baglantiya tiklar

    if any(x in url for x in (".png", ".jpg", ".jpeg")):
        boyut = random.randint(20000, 150000)      # resimler buyuk
    elif any(x in url for x in (".css", ".js")):
        boyut = random.randint(1000, 8000)         # stil/script kucuk
    else:
        boyut = random.randint(500, 40000)         # sayfalar orta

    if durum == 404:
        boyut = random.randint(150, 600)           # hata sayfalari kucuk
    return durum, boyut


def log_satiri(ip, zaman, metot, url, durum, boyut, ua):
    """Tek bir Combined Log Format satiri olusturur."""
    z = zaman.strftime("%d/%b/%Y:%H:%M:%S") + " " + TZ
    return f'{ip} - - [{z}] "{metot} {url} HTTP/1.1" {durum} {boyut} "-" "{ua}"'


def kullanici_oturumlari_uret(ip, ua):
    """Bir kullanicinin gun icindeki tum isteklerini (oturumlarini) uretir."""
    satirlar = []
    for _ in range(random.randint(1, 4)):               # gunde 1-4 oturum
        t = rastgele_zaman()
        for _ in range(random.randint(3, 12)):          # oturumda 3-12 sayfa
            url = random.choice(NORMAL_SAYFALAR)
            durum, boyut = durum_ve_boyut(url)
            satirlar.append((t, log_satiri(ip, t, "GET", url, durum, boyut, ua)))
            # sayfalar arasi birkac saniye gecsin (insan hizi)
            t = t + datetime.timedelta(seconds=random.randint(2, 40))
    return satirlar


def main():
    os.makedirs(os.path.dirname(CIKTI_DOSYASI), exist_ok=True)

    tum_satirlar = []
    for _ in range(NORMAL_KULLANICI_SAYISI):
        ip = rastgele_ip()
        ua = random.choice(NORMAL_UA)
        tum_satirlar.extend(kullanici_oturumlari_uret(ip, ua))

    # Gercek bir log dosyasi kronolojiktir -> zamana gore sirala
    tum_satirlar.sort(key=lambda x: x[0])

    with open(CIKTI_DOSYASI, "w", encoding="utf-8") as f:
        for _zaman, satir in tum_satirlar:
            f.write(satir + "\n")

    print(f"[OK] {len(tum_satirlar)} normal log satiri yazildi -> {CIKTI_DOSYASI}")


if __name__ == "__main__":
    main()
