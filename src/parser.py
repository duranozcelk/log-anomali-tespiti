# =====================================================================
# parser.py  —  ADIM 1: LOG AYRIŞTIRMA (PARSING)
# ---------------------------------------------------------------------
# GÖREV : Ham log dosyasını (düz metin) satır satır okuyup düzenli bir
#         Pandas tablosuna (DataFrame) çevirmek.
#
#   GİRDİ : data/test.log
#   ÇIKTI : data/temiz_log.csv             (temiz tablo, her satır = 1 istek)
#           data/bozuk_satirlar.log        (formata uymayan satırlar)
#           reports/ayristirma_ozeti.txt   (ayrıştırma başarı oranı)
#
# ÇALIŞTIRMA : python src/parser.py
# =====================================================================

import os
import re
from datetime import datetime

import pandas as pd


# =====================================================================
# 1) AYARLAR
# =====================================================================

# Dosya yolları (betik nereden çalıştırılırsa çalıştırılsın doğru yeri bulur)
BU_DOSYA        = os.path.abspath(__file__)         # ...\log-anomali-tespiti\src\parser.py
SRC_KLASORU     = os.path.dirname(BU_DOSYA)         # ...\log-anomali-tespiti\src
PROJE_KLASORU   = os.path.dirname(SRC_KLASORU)      # ...\log-anomali-tespiti
DATA_KLASORU    = os.path.join(PROJE_KLASORU, "data")
REPORTS_KLASORU = os.path.join(PROJE_KLASORU, "reports")

GIRDI_LOG    = os.path.join(DATA_KLASORU, "test.log")
TEMIZ_TABLO  = os.path.join(DATA_KLASORU, "temiz_log.csv")
BOZUK_DOSYA  = os.path.join(DATA_KLASORU, "bozuk_satirlar.log")
OZET_DOSYASI = os.path.join(REPORTS_KLASORU, "ayristirma_ozeti.txt")

# Büyük dosyalar için: her 100.000 satırda bir, biriken satırlar tabloya çevrilir.
# Böylece milyonlarca satır aynı anda bellekte (RAM) ağır bir liste olarak durmaz.
PARCA_BOYUTU = 100000

# Tablonun sütunları
SUTUNLAR = ["ip", "zaman", "metot", "url", "durum", "boyut", "ua"]


# =====================================================================
# 2) REGEX KALIBI
# ---------------------------------------------------------------------
# Bir log satırını tek seferde parçalarına ayıran kalıp.
# (?P<ad>...) yazımı, yakalanan parçaya bir isim verir.
#
# Örnek satır:
# 185.220.101.45 - - [14/Mar/2026:03:12:07 +0300] "GET /admin/config.php HTTP/1.1" 404 153 "-" "python-requests/2.31"
# =====================================================================

LOG_KALIBI = re.compile(
    r'(?P<ip>\S+) \S+ \S+ '                     # 185.220.101.45 - -
    r'\[(?P<zaman>[^\]]+)\] '                   # [14/Mar/2026:03:12:07 +0300]
    r'"(?P<metot>\S+) (?P<url>\S+) [^"]*" '     # "GET /admin/config.php HTTP/1.1"
    r'(?P<durum>\d{3}) '                        # 404
    r'(?P<boyut>\d+|-)'                         # 153   (veri yoksa "-")
    r'(?: "[^"]*" "(?P<ua>[^"]*)")?'            # "-" "python-requests/2.31"  (bu kısım OLMAYABİLİR)
)
# Son satırdaki (?: ... )? yazımı "bu kısım varsa oku, yoksa da sorun değil" demektir.
# Böylece hem Combined (sonunda tarayıcı bilgisi olan) hem de Common
# (tarayıcı bilgisi olmayan) Log Format satırları okunabilir.


# =====================================================================
# 3) TEK BİR SATIRI AYRIŞTIRAN FONKSİYON
# =====================================================================

def satiri_ayristir(satir):
    """Bir log satırını parçalarına ayırır.

    Satır sağlamsa  -> parçaları bir sözlük (dict) olarak döndürür.
    Satır bozuksa   -> None (hiçbir şey) döndürür.
    """
    # --- Kontrol 1: Satır kalıba uyuyor mu? ---
    eslesme = LOG_KALIBI.match(satir)
    if eslesme is None:
        return None                       # Uymadı -> bozuk satır

    # --- Kontrol 2: Zaman okunabiliyor mu? ---
    # "14/Mar/2026:03:12:07 +0300"  -> boşluktan böl, ilk parçayı al -> "14/Mar/2026:03:12:07"
    zaman_metni = eslesme.group("zaman").split(" ")[0]
    try:
        zaman = datetime.strptime(zaman_metni, "%d/%b/%Y:%H:%M:%S")   # metin -> gerçek tarih-saat
    except ValueError:
        return None                       # Okunamadı (ör. "32 Mart") -> bozuk satır

    # --- Boyut: "-" ise 0, değilse sayıya çevir ---
    boyut = eslesme.group("boyut")
    if boyut == "-":
        boyut = 0
    else:
        boyut = int(boyut)                # "153" (metin) -> 153 (sayı)

    # --- Tarayıcı bilgisi: Common Log Format'ta yoktur, o zaman "-" yazılır ---
    ua = eslesme.group("ua")
    if ua is None:
        ua = "-"

    # --- Parçaları bir sözlükte topla (sütun adı -> değer) ---
    kayit = {
        "ip":    eslesme.group("ip"),
        "zaman": zaman,
        "metot": eslesme.group("metot"),
        "url":   eslesme.group("url"),
        "durum": int(eslesme.group("durum")),     # "404" (metin) -> 404 (sayı)
        "boyut": boyut,
        "ua":    ua,
    }
    return kayit


# =====================================================================
# 4) BÜTÜN DOSYAYI OKUYAN FONKSİYON
# =====================================================================

def log_dosyasini_oku(log_yolu, bozuk_yolu):
    """Log dosyasını satır satır okur ve tek bir tablo (DataFrame) döndürür.
    Bozuk satırları silmez, bozuk_yolu dosyasına yazar.

    Döndürür: (tablo, ozet)
        tablo : temiz satırlardan oluşan DataFrame
        ozet  : {"toplam": ..., "basarili": ..., "bozuk": ..., "oran": ...}
    """
    parcalar = []      # Tabloya çevrilmiş parçalar burada birikir
    kayitlar = []      # Şu an doldurulan parçanın satırları (sözlükler)
    basarili = 0       # Sayaç: düzgün okunan satır sayısı
    bozuk = 0          # Sayaç: bozuk satır sayısı

    with open(bozuk_yolu, "w", encoding="utf-8") as bozuk_dosyasi:
        # errors="replace": dosyada okunamayan garip bir karakter varsa program çökmesin
        with open(log_yolu, encoding="utf-8", errors="replace") as log_dosyasi:

            for satir in log_dosyasi:
                satir = satir.strip()            # satır sonundaki "\n" karakterini sil
                if satir == "":
                    continue                     # boş satırı atla, sıradaki satıra geç

                kayit = satiri_ayristir(satir)

                if kayit is None:                # Bozuk -> ayrı dosyaya yaz
                    bozuk_dosyasi.write(satir + "\n")
                    bozuk = bozuk + 1
                else:                            # Sağlam -> listeye ekle
                    kayitlar.append(kayit)
                    basarili = basarili + 1

                # Parça doldu mu? -> tabloya çevir, listeyi boşalt
                if len(kayitlar) == PARCA_BOYUTU:
                    parcalar.append(pd.DataFrame(kayitlar))
                    kayitlar = []

    # Döngü bitti. Son parçada kalan satırları da tabloya çevir.
    if len(kayitlar) > 0:
        parcalar.append(pd.DataFrame(kayitlar))

    # Bütün parçaları alt alta birleştirip tek tablo yap
    if len(parcalar) > 0:
        tablo = pd.concat(parcalar, ignore_index=True)
    else:
        tablo = pd.DataFrame(columns=SUTUNLAR)   # hiç sağlam satır yoksa boş tablo

    # Ayrıştırma başarı oranı
    toplam = basarili + bozuk
    if toplam > 0:
        oran = 100 * basarili / toplam
    else:
        oran = 0

    ozet = {"toplam": toplam, "basarili": basarili, "bozuk": bozuk, "oran": oran}
    return tablo, ozet


# =====================================================================
# 5) ANA PROGRAM
# =====================================================================

def main():
    if not os.path.exists(GIRDI_LOG):
        print("HATA: test.log bulunamadı.")
        print("Önce şunları çalıştır: python tools/normal_trafik_uret.py ve python tools/saldiri_uret.py")
        return

    # --- Adım 1: Logu oku ve tabloya çevir ---
    tablo, ozet = log_dosyasini_oku(GIRDI_LOG, BOZUK_DOSYA)

    # --- Adım 2: Temiz tabloyu CSV olarak kaydet (Excel ile de açılabilir) ---
    tablo.to_csv(TEMIZ_TABLO, index=False)

    # --- Adım 3: Ayrıştırma özetini hazırla, ekrana ve dosyaya yaz ---
    ozet_metni = (
        "AYRIŞTIRMA ÖZETİ\n"
        f"Okunan dosya        : {GIRDI_LOG}\n"
        f"Toplam satır        : {ozet['toplam']}\n"
        f"Başarıyla ayrıştı   : {ozet['basarili']}\n"
        f"Bozuk (ayrı dosyada): {ozet['bozuk']}\n"
        f"Başarı oranı        : %{ozet['oran']:.2f}\n"
    )
    print(ozet_metni)

    os.makedirs(REPORTS_KLASORU, exist_ok=True)
    with open(OZET_DOSYASI, "w", encoding="utf-8") as dosya:
        dosya.write(ozet_metni)

    # --- Adım 4: Tablonun ilk 5 satırını ve sütun türlerini göster ---
    print("Tablonun ilk 5 satırı:")
    print(tablo.head().to_string())
    print()
    print("Sütun türleri (zaman = tarih-saat, durum ve boyut = sayı olmalı):")
    print(tablo.dtypes.to_string())
    print()
    print(f"Kaydedildi: {TEMIZ_TABLO}")
    print(f"Kaydedildi: {BOZUK_DOSYA}")
    print(f"Kaydedildi: {OZET_DOSYASI}")


# Bu dosya doğrudan çalıştırılınca main() başlar.
# Başka bir dosya "from parser import log_dosyasini_oku" yaparsa main() çalışmaz.
if __name__ == "__main__":
    main()
