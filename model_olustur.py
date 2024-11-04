import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

# SQL Bağlantısı
engine = create_engine('mssql+pyodbc://usesen:usesen@DESKTOP-6QR83E3\\UGURMSSQL/FSM_Tickets?driver=SQL+Server')

# Eğitim verilerini çek
query = """
SELECT 
    t1.Bolge,
    t1.Teknisyen,
    MONTH(t1.Olusturma_Tarihi) as Ay,
    COUNT(*) as Ticket_Sayisi,
    COUNT(*) * 1.0 / 
        (SELECT COUNT(*) 
         FROM Tickets t2 
         WHERE t2.Bolge = t1.Bolge 
         AND t2.Teknisyen = t1.Teknisyen 
         AND YEAR(t2.Olusturma_Tarihi) = 2024 
         AND MONTH(t2.Olusturma_Tarihi) <= 3) as Oran
FROM Tickets t1
WHERE 
    YEAR(t1.Olusturma_Tarihi) = 2024
    AND MONTH(t1.Olusturma_Tarihi) <= 3
GROUP BY 
    t1.Bolge,
    t1.Teknisyen,
    MONTH(t1.Olusturma_Tarihi)
"""

df = pd.read_sql(query, engine)

# Feature'ları hazırla
X = pd.get_dummies(df[['Bolge', 'Teknisyen', 'Ay']])
y = df['Ticket_Sayisi']

# Mevsimsel faktörleri ekleyelim

# Model oluştur ve eğit
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# ONNX'e çevir
initial_type = [('float_input', FloatTensorType([None, X.shape[1]]))]
onx = convert_sklearn(model, initial_types=initial_type)

# ONNX modelini kaydet
with open("D:/PhytonEgitimleri/ticket_tahmin_modeli.onnx", "wb") as f:
    f.write(onx.SerializeToString())

print("Model başarıyla oluşturuldu: ticket_tahmin_modeli.onnx")
