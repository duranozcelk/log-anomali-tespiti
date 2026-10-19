# Log Anomali Tespiti

Web sunucu (Nginx/Apache) erişim loglarında şüpheli davranışları tespit eden bir üniversite projesi. Ham log satırları Regex ile ayrıştırılır, IP ve zaman pencerelerine göre öznitelikler çıkarılır. SQL Injection ve XSS kalıpları kural tabanlı bir filtreyle aranır, olağandışı trafik ise **Isolation Forest** ile tespit edilir. Sonuçlar Precision, Recall, F1 ve False Positive oranıyla değerlendirilir.

## Kurulum

Python 3.10 veya üstü gereklidir.

1. Sanal ortamı oluşturun:

   ```bash
   python -m venv venv
   ```

2. Sanal ortamı etkinleştirin:

   - Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - Windows (CMD):
     ```cmd
     venv\Scripts\activate.bat
     ```
   - Linux / macOS:
     ```bash
     source venv/bin/activate
     ```

3. Bağımlılıkları kurun:

   ```bash
   pip install -r requirements.txt
   ```

## Klasör Yapısı

```
log-anomali-tespiti/
├── data/
│   ├── raw/            # Ham log dosyaları (git'e eklenmez)
│   └── processed/      # İşlenmiş veriler
├── src/
│   ├── parser.py       # Log satırlarını Regex ile ayrıştırma
│   ├── features.py     # IP ve zaman penceresi öznitelikleri
│   ├── rules.py        # SQL Injection / XSS kural tabanlı filtre
│   ├── detector.py     # Isolation Forest ile anomali tespiti
│   └── evaluate.py     # Precision, Recall, F1, FP oranı
├── notebooks/
│   └── 01_inceleme.py  # İlk inceleme ve deneme betiği
├── reports/            # Üretilen raporlar
├── requirements.txt
├── README.md
└── .gitignore
```
