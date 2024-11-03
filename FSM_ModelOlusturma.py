import pyodbc
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
import tf2onnx
import onnx

# MSSQL veritabanına bağlanma
conn = pyodbc.connect('DRIVER={SQL Server};SERVER=DESKTOP-6QR83E3\\UGURMSSQL;DATABASE=FSM_Tickets;UID=usesen;PWD=usesen')

# Veriyi çekme
query = "SELECT * FROM Tickets"
df = pd.read_sql(query, conn)
conn.close()

# 50 bin rastgele kayıt seçme
df = df.sample(n=50000, random_state=42)

# Verinin başına göz atalım
print(df.head())

# Örnek olarak sadece bazı sütunları kullanıyoruz
df = df[["Bolge", "Oncelik", "Kategori", "Hedef_Cozum_Suresi_dk", "Gercek_Cozum_Suresi_dk", "Musteri_Memnuniyeti"]]

# Kategorik verileri sayısal verilere dönüştürme (One-Hot Encoding)
df = pd.get_dummies(df, columns=["Bolge", "Oncelik", "Kategori"])

# Musteri_Memnuniyeti değerlerini 0-1 aralığına normalleştirme
min_value = df["Musteri_Memnuniyeti"].min()
max_value = df["Musteri_Memnuniyeti"].max()
df["Musteri_Memnuniyeti"] = (df["Musteri_Memnuniyeti"] - min_value) / (max_value - min_value)

# Normalizasyon sonrası min ve max değerleri doğrulama
print("Düzgün Normalizasyon sonrası Musteri_Memnuniyeti Min Değer:", df["Musteri_Memnuniyeti"].min())
print("Düzgün Normalizasyon sonrası Musteri_Memnuniyeti Max Değer:", df["Musteri_Memnuniyeti"].max())

# Giriş (X) ve çıkış (y) verilerini ayırma
X = df.drop("Musteri_Memnuniyeti", axis=1)
y = df["Musteri_Memnuniyeti"]

# Eğitim ve test setlerine ayırma
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Modelin beklediği veri tipine dönüştürme
X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
y_train = y_train.astype('float32')
y_test = y_test.astype('float32')

# Modeli oluşturma
model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(1)  # Çıkış katmanı, müşteri memnuniyetini tahmin eder
])

# Modeli derleme
model.compile(optimizer='adam', loss='mse', metrics=['mae'])

# Modeli eğitme
history = model.fit(X_train, y_train, epochs=10, validation_data=(X_test, y_test))

# Modelin performansını değerlendirme
loss, mae = model.evaluate(X_test, y_test)
print(f"Test Mean Absolute Error: {mae}")

# Modeli ONNX formatına çevirme ve kaydetme
onnx_model, _ = tf2onnx.convert.from_keras(model)
onnx.save_model(onnx_model, "model.onnx")
