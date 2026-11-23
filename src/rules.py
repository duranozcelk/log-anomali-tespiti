# =====================================================================
# rules.py  —  ADIM 3 / 1. AŞAMA: KURAL TABANLI FİLTRE
# ---------------------------------------------------------------------
# GÖREV : Her isteğin URL'sini bilinen saldırı kalıplarıyla (Regex)
#         karşılaştırmak. Kalıba uyan istek, modele sorulmadan
#         "Saldırı" etiketi alır ve hangi kuralın eşleştiği yazılır.
#
#   GİRDİ : data/temiz_log.csv               (3. haftanın çıktısı)
#   ÇIKTI : data/kural_eslesmeleri.csv       (kurala uyan her İSTEK, tek tek)
#           reports/kural_eslesme_raporu.csv (kurala uyan her IP, özet)
#
# ÇALIŞTIRMA : python src/rules.py
# =====================================================================

import os
import re
from urllib.parse import unquote

import pandas as pd


# =====================================================================
# 1) AYARLAR
# =====================================================================

BU_DOSYA        = os.path.abspath(__file__)         # ...\log-anomali-tespiti\src\rules.py
SRC_KLASORU     = os.path.dirname(BU_DOSYA)         # ...\log-anomali-tespiti\src
PROJE_KLASORU   = os.path.dirname(SRC_KLASORU)      # ...\log-anomali-tespiti
DATA_KLASORU    = os.path.join(PROJE_KLASORU, "data")
REPORTS_KLASORU = os.path.join(PROJE_KLASORU, "reports")

TEMIZ_TABLO      = os.path.join(DATA_KLASORU, "temiz_log.csv")
ESLESME_DOSYASI  = os.path.join(DATA_KLASORU, "kural_eslesmeleri.csv")
RAPOR_DOSYASI    = os.path.join(REPORTS_KLASORU, "kural_eslesme_raporu.csv")


# =====================================================================
# 2) KURAL LİSTESİ
# ---------------------------------------------------------------------
# Her kural 3 parçadan oluşur:  (kuralın adı, saldırı türü, aranacak kalıp)
#
# re.IGNORECASE -> büyük/küçük harf fark etmez
#                  (UNION SELECT, union select, UnIoN SeLeCt hepsi yakalanır)
#
# Kalıplarda geçen işaretler:
#   \s*  -> arada boşluk OLABİLİR de OLMAYABİLİR de
#   \s+  -> arada EN AZ BİR boşluk olmalı
#   \d+  -> bir veya daha fazla rakam
#   '?   -> tek tırnak olabilir de olmayabilir de
#   ( | )-> "ya bu ya şu"
# =====================================================================

KURALLAR = [
    # ---------------- SQL INJECTION ----------------
    ("' OR 1=1",      "SQL Injection", re.compile(r"'\s*or\s+'?\d+'?\s*=\s*'?\d+", re.IGNORECASE)),
    #   yakalar: 5' OR 1=1      5' or '1'='1

    ("UNION SELECT",  "SQL Injection", re.compile(r"union\s+(all\s+)?select", re.IGNORECASE)),
    #   yakalar: 1 UNION SELECT ...      1 union all select ...

    ("DROP TABLE",    "SQL Injection", re.compile(r"drop\s+table", re.IGNORECASE)),
    #   yakalar: 1;DROP TABLE kullanicilar

    ("' -- (yorum)",  "SQL Injection", re.compile(r"'\s*--")),
    #   yakalar: admin'--   (şifre kontrolünü yorum satırı yapıp atlatma)

    # ---------------- XSS (Cross-Site Scripting) ----------------
    ("<script>",      "XSS", re.compile(r"<\s*script", re.IGNORECASE)),
    #   yakalar: <script>alert(1)</script>     <SCRIPT>

    ("javascript:",   "XSS", re.compile(r"javascript\s*:", re.IGNORECASE)),
    #   yakalar: ?url=javascript:alert(1)

    ("onerror= / onload=", "XSS", re.compile(r"on(error|load)\s*=", re.IGNORECASE)),
    #   yakalar: <img src=x onerror=alert(1)>     <svg onload=alert(1)>
]


# =====================================================================
# 3) TEK BİR URL'Yİ KONTROL EDEN FONKSİYON
# =====================================================================

def kural_bul(url):
    """Bir URL'yi önce çözer, sonra kurallarla karşılaştırır.

    Döndürür: (cozulmus_url, kural_adi, saldiri_turu)
              Hiçbir kurala uymuyorsa kural_adi ve saldiri_turu = None
    """
    # Adım 1: URL'yi çöz. Saldırganlar kalıbı gizlemek için karakterleri kodlar.
    #   "/urun.php?id=5%27%20OR%201=1--"  ->  "/urun.php?id=5' OR 1=1--"
    #   %27 -> '   (tek tırnak)      %20 -> boşluk      %3C -> <      %3E -> >
    cozulmus = unquote(url)

    # Adım 2: Kuralları sırayla dene. İLK eşleşen kural yazılır.
    for kural_adi, saldiri_turu, kalip in KURALLAR:
        if kalip.search(cozulmus):              # search: kalıp URL'nin HERHANGİ bir yerinde geçiyor mu?
            return cozulmus, kural_adi, saldiri_turu

    # Hiçbir kurala uymadı
    return cozulmus, None, None


# =====================================================================
# 4) BÜTÜN TABLOYA KURALLARI UYGULAYAN FONKSİYON
# =====================================================================

def kurallari_uygula(tablo):
    """Tablodaki her isteğin URL'sini kontrol eder ve 3 yeni sütun ekler:
       cozulmus_url, kural, saldiri_turu
    (Kurala uymayan isteklerde kural ve saldiri_turu boş kalır.)
    """
    tablo = tablo.copy()            # Orijinal tabloyu bozmamak için kopyası üzerinde çalış

    cozulmusler = []
    kurallar = []
    turler = []

    for url in tablo["url"]:        # Her isteğin URL'sine tek tek bak
        cozulmus, kural, tur = kural_bul(url)
        cozulmusler.append(cozulmus)
        kurallar.append(kural)
        turler.append(tur)

    tablo["cozulmus_url"] = cozulmusler
    tablo["kural"] = kurallar
    tablo["saldiri_turu"] = turler
    return tablo


# =====================================================================
# 5) IP BAZINDA ÖZET ÇIKARAN FONKSİYON
# =====================================================================

def benzersizleri_birlestir(degerler):
    """['UNION SELECT', '<script>', 'UNION SELECT'] -> '<script>; UNION SELECT'
    (tekrarları atar, alfabetik sıralar, aralarına '; ' koyar)"""
    return "; ".join(sorted(set(degerler)))


def ip_ozeti_cikar(eslesenler):
    """Kurala uyan istekleri IP'ye göre gruplar. Her saldırgan IP için:
    kaç isteği kurala uydu, hangi türler ve hangi kurallar eşleşti."""
    ozet = eslesenler.groupby("ip").agg(
        eslesen_istek = ("kural", "count"),
        saldiri_turu  = ("saldiri_turu", benzersizleri_birlestir),
        kurallar      = ("kural", benzersizleri_birlestir),
    )
    ozet = ozet.reset_index()

    # Raporundaki Tablo 4'e uygun etiket: kurala uyan IP doğrudan "Saldırı"
    ozet["etiket"] = "Saldırı"

    # Sütunları okunaklı bir sıraya koy ve en çok eşleşeni en üste al
    ozet = ozet[["ip", "etiket", "saldiri_turu", "kurallar", "eslesen_istek"]]
    ozet = ozet.sort_values("eslesen_istek", ascending=False)
    return ozet


# =====================================================================
# 6) ANA PROGRAM
# =====================================================================

def main():
    if not os.path.exists(TEMIZ_TABLO):
        print("HATA: temiz_log.csv bulunamadı.")
        print("Önce şunu çalıştır: python src/parser.py")
        return

    # --- Adım 1: Temiz tabloyu oku ---
    tablo = pd.read_csv(TEMIZ_TABLO, parse_dates=["zaman"])
    print(f"Okundu: {len(tablo)} istek, {tablo['ip'].nunique()} farklı IP")
    print()

    # --- Adım 2: Kuralları uygula ---
    tablo = kurallari_uygula(tablo)

    # --- Adım 3: Sadece kurala uyan istekleri ayır ---
    # notna() -> "boş değil mi?"  (kural sütunu doluysa, o istek bir kurala uymuş demektir)
    eslesenler = tablo[tablo["kural"].notna()]

    # --- Adım 4: Kaydet ---
    sutunlar = ["ip", "zaman", "url", "cozulmus_url", "kural", "saldiri_turu"]
    # utf-8-sig: Excel'in Türkçe karakterleri (ı, ş, ğ) doğru göstermesi için
    eslesenler[sutunlar].to_csv(ESLESME_DOSYASI, index=False, encoding="utf-8-sig")

    os.makedirs(REPORTS_KLASORU, exist_ok=True)
    ip_ozeti = ip_ozeti_cikar(eslesenler)
    ip_ozeti.to_csv(RAPOR_DOSYASI, index=False, encoding="utf-8-sig")

    # --- Adım 5: Ekrana özet yaz ---
    print("KURAL EŞLEŞME ÖZETİ")
    print(f"Kurala uyan istek : {len(eslesenler)} / {len(tablo)}")
    print(f"Kurala uyan IP    : {len(ip_ozeti)}")
    print()

    print("Hangi kural kaç kez eşleşti:")
    print(eslesenler["kural"].value_counts().to_string())
    print()

    print("Kurala uyan IP'ler (kural eşleşme raporu):")
    print(ip_ozeti.to_string(index=False))
    print()

    # URL çözmenin (unquote) neden gerekli olduğunu gösteren örnekler
    print("Kodlanmış URL'lerin çözülmüş hali (birkaç örnek):")
    kodlular = eslesenler[eslesenler["url"] != eslesenler["cozulmus_url"]]
    ornekler = kodlular.drop_duplicates("url").head(3)
    for i in range(len(ornekler)):
        print(f"  logda   : {ornekler['url'].iloc[i]}")
        print(f"  çözülünce: {ornekler['cozulmus_url'].iloc[i]}")
        print()

    print(f"Kaydedildi: {ESLESME_DOSYASI}")
    print(f"Kaydedildi: {RAPOR_DOSYASI}")


# Bu dosya doğrudan çalıştırılınca main() başlar.
# 6. haftada detector.py "from rules import kurallari_uygula" yapacak; o zaman main() çalışmaz.
if __name__ == "__main__":
    main()
