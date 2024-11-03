import pandas as pd
import onnxruntime as rt
import numpy as np

# Test verisi oluştur
test_data = pd.DataFrame({
    'Tarih_Numeric': [0],  # Minimum tarihten itibaren gün sayısı
    'Haftanin_Gunu': [1],  # Pazartesi
    'Ay': [1],            # Ocak
    'Saat': [10],         # Saat 10
    'Is_Gununde_mi': [1], 
    'Mesai_Saatinde_mi': [1]
})

# Feature bilgilerini oku
import json
with open('feature_info.json', 'r') as f:
    feature_info = json.load(f)

# One-hot encoding için boş kolonlar ekle
for feature in feature_info['feature_names']:
    if feature not in test_data.columns:
        test_data[feature] = 0

# Test verisi için değerleri ayarla
test_data['Bolge_İstanbul-Avrupa'] = 1
test_data['Kategori_Donanım'] = 1
test_data['Alt_Kategori_PC Arıza'] = 1

# Kolonları doğru sıraya koy
test_data = test_data[feature_info['feature_names']]

# ONNX ile tahmin
session = rt.InferenceSession("ticket_tahmin_modeli.onnx")
input_name = session.get_inputs()[0].name
pred_onx = session.run(None, {input_name: test_data.astype(np.float32).values})[0]

print(f"Python tarafında tahmin: {pred_onx[0]}")

# Debug için feature değerlerini yazdır
print("\nFeature değerleri:")
for col in test_data.columns:
    print(f"{col}: {test_data[col].values[0]}") 