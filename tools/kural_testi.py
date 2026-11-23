# =====================================================================
# kural_testi.py
# ---------------------------------------------------------------------
# GÖREV : rules.py'deki kuralları elle hazırlanmış URL'lerle denemek.
#   - 12 zararlı URL (bir kısmı %27 gibi KODLANMIŞ)  -> yakalanmalı
#   - 6 masum URL (içinde "script", "select" gibi kelimeler geçen) -> yakalanMAMALI
# Ayrıca URL çözme (unquote) yapılmasaydı hangi saldırıların kaçacağını gösterir.
#
# ÇALIŞTIRMA : python tools/kural_testi.py
# =====================================================================

import os
import sys

BU_DOSYA      = os.path.abspath(__file__)          # ...\log-anomali-tespiti\tools\kural_testi.py
TOOLS_KLASORU = os.path.dirname(BU_DOSYA)          # ...\log-anomali-tespiti\tools
PROJE_KLASORU = os.path.dirname(TOOLS_KLASORU)     # ...\log-anomali-tespiti
SRC_KLASORU   = os.path.join(PROJE_KLASORU, "src")

# rules.py "src" klasöründe. Python'a "modülleri orada da ara" diyoruz.
sys.path.insert(0, SRC_KLASORU)
from rules import kural_bul, KURALLAR


# =====================================================================
# 1) DENEME URL'LERİ:  (url, beklenen sonuç)
#    beklenen sonuç: "SQL Injection", "XSS" veya None (masum)
# =====================================================================

DENEMELER = [
    # ---------- ZARARLI: kodlanmamış ----------
    ("/urun.php?id=5' OR 1=1--",                     "SQL Injection"),
    ("/ara?q=<script>alert(1)</script>",             "XSS"),
    ("/profil?ad=<img/src=x/onerror=alert(1)>",      "XSS"),
    ("/sayfa?url=javascript:alert(1)",               "XSS"),

    # ---------- ZARARLI: KODLANMIŞ (unquote gerekli) ----------
    ("/urun.php?id=5%27%20OR%201=1--",               "SQL Injection"),   # 5' OR 1=1--
    ("/urun.php?id=5%27%20OR%20%271%27=%271",        "SQL Injection"),   # 5' OR '1'='1
    ("/ara?q=1%20UNION%20SELECT%20kullanici,sifre",  "SQL Injection"),   # 1 UNION SELECT ...
    ("/ara?q=1%20union%20all%20select%20*",          "SQL Injection"),   # küçük harf + ALL
    ("/urun.php?id=1;DROP%20TABLE%20kullanicilar",   "SQL Injection"),   # 1;DROP TABLE ...
    ("/login?user=admin%27--",                       "SQL Injection"),   # admin'--
    ("/ara?q=%3Cscript%3Ealert(1)%3C/script%3E",     "XSS"),             # <script>...
    ("/ara?q=%3CSCRIPT%3Ealert(1)",                  "XSS"),             # büyük harf <SCRIPT>

    # ---------- MASUM: yakalanmamalı (yanlış alarm testi) ----------
    ("/urunler",                                     None),
    ("/urun.php?id=12",                              None),
    ("/blog/javascript-dersleri",                    None),   # "javascript" var ama ":" yok
    ("/blog/script-yazmak",                          None),   # "script" var ama "<" yok
    ("/ara?q=select%20kitap",                        None),   # "select" var ama "union" yok
    ("/ara?q=kitap%20or%20defter",                   None),   # "or" var ama tırnak ve 1=1 yok
]


# =====================================================================
# 2) "unquote OLMASAYDI" sonucunu bulan fonksiyon
# =====================================================================

def cozmeden_kontrol(url):
    """Aynı kuralları, URL'yi ÇÖZMEDEN uygular (karşılaştırma için)."""
    for kural_adi, saldiri_turu, kalip in KURALLAR:
        if kalip.search(url):
            return saldiri_turu
    return None


# =====================================================================
# 3) TEST
# =====================================================================

def main():
    gecen = 0
    kalan = 0
    cozmeden_kacan = 0

    print(f"{'SONUÇ':8s} {'BEKLENEN':14s} {'BULUNAN':14s} {'unquote olmasaydı':18s} URL")
    print("-" * 110)

    for url, beklenen in DENEMELER:
        cozulmus, kural, bulunan = kural_bul(url)
        cozmeden = cozmeden_kontrol(url)

        if bulunan == beklenen:
            sonuc = "GEÇTİ"
            gecen = gecen + 1
        else:
            sonuc = "KALDI"
            kalan = kalan + 1

        # Zararlı bir URL, çözülmeden bakılınca kaçıyorsa bunu işaretle
        if beklenen is not None and cozmeden is None:
            cozmeden_metni = "KAÇARDI"
            cozmeden_kacan = cozmeden_kacan + 1
        elif beklenen is not None:
            cozmeden_metni = "yakalanırdı"
        else:
            cozmeden_metni = "-"

        print(f"{sonuc:8s} {str(beklenen):14s} {str(bulunan):14s} {cozmeden_metni:18s} {url}")

    zararli_sayisi = 0
    for url, beklenen in DENEMELER:
        if beklenen is not None:
            zararli_sayisi = zararli_sayisi + 1

    print()
    print(f"SONUÇ: {gecen} test geçti, {kalan} test kaldı.")
    print(f"URL çözülmeseydi {zararli_sayisi} zararlı URL'den {cozmeden_kacan} tanesi KAÇARDI.")


if __name__ == "__main__":
    main()
