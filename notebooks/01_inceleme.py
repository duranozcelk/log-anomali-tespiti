import re
import pandas as pd
from sklearn.ensemble import IsolationForest

# 1) Log formatını test et
satir = '185.220.101.45 - - [14/Mar/2026:03:12:07 +0300] "GET /admin/config.php HTTP/1.1" 404 153 "-" "python-requests/2.31"'
kalip = r'(?P<ip>\S+) \S+ \S+ \[(?P<zaman>[^\]]+)\] "(?P<metot>\S+) (?P<url>\S+) [^"]*" (?P<durum>\d{3}) (?P<boyut>\d+|-)'
print(re.match(kalip, satir).groupdict())
print(pd.to_datetime("14/Mar/2026:03:12:07 +0300", format="%d/%b/%Y:%H:%M:%S %z"))

# 2) Isolation Forest skorlarını gör
X = pd.DataFrame(
    {"istek_1dk": [5, 7, 6, 8, 4, 240],
     "hata_orani": [0.02, 0.03, 0.01, 0.02, 0.04, 0.96]},
    index=["ip1", "ip2", "ip3", "ip4", "ip5", "saldirgan"],
)
model = IsolationForest(n_estimators=100, contamination=0.17, random_state=42).fit(X)

sonuc = X.copy()
sonuc["skor"] = -model.score_samples(X)   # 1'e yaklaştıkça daha şüpheli
sonuc["etiket"] = model.predict(X)        # 1 = normal, -1 = anomali
print(sonuc.round(2))
