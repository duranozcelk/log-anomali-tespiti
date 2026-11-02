# =====================================================================
# parser_testi.py
# ---------------------------------------------------------------------
# GÖREV : parser.py'yi farklı türde log satırlarıyla denemek.
#         5 sağlam + 4 bilerek bozulmuş satır hazırlanır; parser'ın
#         sağlamları tabloya alıp bozukları ayırdığı kontrol edilir.
#
# ÇALIŞTIRMA : python tools/parser_testi.py
# =====================================================================

import os
import sys

# Dosya yolları
BU_DOSYA      = os.path.abspath(__file__)          # ...\log-anomali-tespiti\tools\parser_testi.py
TOOLS_KLASORU = os.path.dirname(BU_DOSYA)          # ...\log-anomali-tespiti\tools
PROJE_KLASORU = os.path.dirname(TOOLS_KLASORU)     # ...\log-anomali-tespiti
SRC_KLASORU   = os.path.join(PROJE_KLASORU, "src")
DATA_KLASORU  = os.path.join(PROJE_KLASORU, "data")

ORNEK_LOG   = os.path.join(DATA_KLASORU, "ornek_satirlar.log")
ORNEK_BOZUK = os.path.join(DATA_KLASORU, "ornek_bozuk.log")

# parser.py "src" klasöründe. Python'a "modülleri orada da ara" diyoruz.
sys.path.insert(0, SRC_KLASORU)
from parser import log_dosyasini_oku


# =====================================================================
# 1) DENEME SATIRLARI
# =====================================================================

ORNEK_SATIRLAR = [
    # ---------- 5 SAĞLAM SATIR ----------
    # 1) Raporundaki örnek satır (Nginx, Combined Log Format)
    '185.220.101.45 - - [14/Mar/2026:03:12:07 +0300] "GET /admin/config.php HTTP/1.1" 404 153 "-" "python-requests/2.31"',
    # 2) Apache, Common Log Format (sonunda tarayıcı bilgisi YOK)
    '127.0.0.1 - frank [14/Mar/2026:13:55:36 +0300] "GET /index.html HTTP/1.0" 200 2326',
    # 3) Boyutu "-" olan satır (304: veri gönderilmedi)
    '85.12.40.7 - - [14/Mar/2026:10:15:51 +0300] "GET /sepet HTTP/1.1" 304 - "-" "Mozilla/5.0"',
    # 4) URL'si kodlanmış SQL Injection
    '193.34.76.22 - - [14/Mar/2026:15:40:00 +0300] "GET /urun.php?id=5%27%20OR%201=1-- HTTP/1.1" 500 800 "-" "curl/8.4.0"',
    # 5) Brute-force denemesi (POST)
    '185.220.101.45 - - [14/Mar/2026:02:15:00 +0300] "POST /login HTTP/1.1" 401 350 "-" "python-requests/2.31.0"',

    # ---------- 4 BOZUK SATIR ----------
    # 6) Log satırıyla hiç ilgisi olmayan metin
    'bu satir tamamen bozuk bir metin',
    # 7) Yarıda kesilmiş satır (disk dolunca ya da sunucu çökünce olur)
    '185.220.101.45 - - [14/Mar/2026:03:12:07 +0300] "GET /admin',
    # 8) Kalıba uyuyor ama tarih geçersiz (32 Mart diye bir gün yok)
    '10.0.0.5 - - [32/Mar/2026:10:00:00 +0300] "GET / HTTP/1.1" 200 512 "-" "Mozilla/5.0"',
    # 9) Durum kodu 3 haneli değil
    '10.0.0.6 - - [14/Mar/2026:10:00:00 +0300] "GET / HTTP/1.1" 20 512 "-" "Mozilla/5.0"',
]


# =====================================================================
# 2) KONTROL FONKSİYONU
# =====================================================================

gecen = 0
kalan = 0

def kontrol(aciklama, sonuc):
    """sonuc True ise GEÇTİ, False ise KALDI yazar ve sayar."""
    global gecen, kalan            # fonksiyon dışındaki sayaçları değiştirebilmek için
    if sonuc:
        print("  [GEÇTİ] " + aciklama)
        gecen = gecen + 1
    else:
        print("  [KALDI] " + aciklama)
        kalan = kalan + 1


# =====================================================================
# 3) TEST
# =====================================================================

def main():
    # Deneme satırlarını bir dosyaya yaz
    os.makedirs(DATA_KLASORU, exist_ok=True)
    with open(ORNEK_LOG, "w", encoding="utf-8") as dosya:
        for satir in ORNEK_SATIRLAR:
            dosya.write(satir + "\n")

    # parser.py ile oku
    tablo, ozet = log_dosyasini_oku(ORNEK_LOG, ORNEK_BOZUK)

    print("Parser'ın ürettiği tablo:")
    print(tablo.to_string())
    print()

    print("Bozuk dosyasına ayrılan satırlar:")
    with open(ORNEK_BOZUK, encoding="utf-8") as dosya:
        for satir in dosya:
            print("  " + satir.strip())
    print()

    print("Kontroller:")
    kontrol("5 sağlam satır tabloya alındı",          len(tablo) == 5)
    kontrol("4 bozuk satır ayrı dosyaya yazıldı",      ozet["bozuk"] == 4)
    kontrol("Başarı oranı 5/9 = %55,56",               round(ozet["oran"], 2) == 55.56)
    kontrol("Raporundaki örnek satırın IP'si doğru",   tablo["ip"][0] == "185.220.101.45")
    kontrol("Raporundaki örnek satırın URL'si doğru",  tablo["url"][0] == "/admin/config.php")
    kontrol("Common formatta tarayıcı yerine '-' var", tablo["ua"][1] == "-")
    kontrol("Boyutu '-' olan satır 0 yapıldı",         tablo["boyut"][2] == 0)
    kontrol("Kodlu URL olduğu gibi duruyor (5. haftada çözülecek)",
            tablo["url"][3] == "/urun.php?id=5%27%20OR%201=1--")
    kontrol("Zaman sütunu gerçek tarih-saat türünde",  str(tablo["zaman"].dtype).startswith("datetime64"))
    kontrol("Durum kodu sayı türünde",                 str(tablo["durum"].dtype).startswith("int"))

    print()
    print(f"SONUÇ: {gecen} kontrol geçti, {kalan} kontrol kaldı.")


if __name__ == "__main__":
    main()
