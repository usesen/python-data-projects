import pandas as pd
import pyodbc
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, RobustScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, accuracy_score

# Veritabanı bağlantısı için SQLAlchemy kullanımı
from sqlalchemy import create_engine

# Uyarıları gizle
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Veritabanı bağlantısı
engine = create_engine('mssql+pyodbc://usesen:usesen@DESKTOP-6QR83E3\\UGURMSSQL/FSM_Tickets?driver=SQL+Server')

# Veri çekme sorgusu
query = """
WITH TeknisyenVerileri AS (
    SELECT 
        [Teknisyen],
        [Oncelik],
        [Kategori],
        [Bolge],
        ROW_NUMBER() OVER (PARTITION BY [Teknisyen] ORDER BY NEWID()) as RowNum
    FROM Tickets
)
SELECT TOP 80000  -- Her teknisyen için 10,000 veri
    Teknisyen, Oncelik, Kategori, Bolge
FROM TeknisyenVerileri
WHERE RowNum <= 100  -- Her teknisyenden eşit sayıda
ORDER BY NEWID()
"""

df = pd.read_sql(query, engine)

# Kategorik verileri dönüştürme
categorical_columns = ['Oncelik', 'Kategori', 'Bolge']
df_encoded = pd.get_dummies(df, columns=categorical_columns)

# X ve y'yi ayırma
X = df_encoded.drop('Teknisyen', axis=1)
y = df['Teknisyen']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Veri standardizasyonunu güçlendirelim
scaler = RobustScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Label encoding
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
y_train = le.fit_transform(y_train)
y_test = le.transform(y_test)

# Veri tiplerini düzeltme
X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
y_train = y_train.astype('float32')
y_test = y_test.astype('float32')

# Sınıf ağırlıklarını daha agresif ayarlayalım
class_weights = compute_class_weight(
    class_weight='balanced',
    classes=np.unique(y_train),
    y=y_train
)
class_weight_dict = dict(enumerate(class_weights * 1.5))  # 1.5 ile çarpıyoruz

# 1. Veri dengeleme
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline

# Combine SMOTE and undersampling
steps = [('smote', SMOTE(random_state=42)),
         ('undersampling', RandomUnderSampler(random_state=42))]
pipeline = Pipeline(steps=steps)

X_train_balanced, y_train_balanced = pipeline.fit_resample(X_train, y_train)

# 2. Model mimarisi
model = Sequential([
    Dense(256, activation='relu', input_shape=(X_train.shape[1],)),
    BatchNormalization(),
    Dropout(0.3),
    
    Dense(128, activation='relu'),
    BatchNormalization(),
    Dropout(0.3),
    
    Dense(64, activation='relu'),
    BatchNormalization(),
    Dropout(0.2),
    
    Dense(len(np.unique(y_train)), activation='softmax')
])

# 3. Custom loss function
def custom_loss(y_true, y_pred):
    # Normal categorical crossentropy
    cce = tf.keras.losses.SparseCategoricalCrossentropy()(y_true, y_pred)
    # Add penalty for uneven distribution
    distribution_penalty = tf.reduce_mean(tf.square(tf.reduce_mean(y_pred, axis=0) - 0.125))
    return cce + 0.1 * distribution_penalty

# 4. Compile
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss=custom_loss,
    metrics=['accuracy']
)

# 5. Training
history = model.fit(
    X_train_balanced,
    y_train_balanced,
    epochs=100,
    batch_size=64,
    validation_split=0.2,
    callbacks=[
        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
        ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5)
    ],
    shuffle=True
)

# Model değerlendirme
y_pred = model.predict(X_test)
y_pred_classes = np.argmax(y_pred, axis=1)

# Sonuçları yazdırma
print("\nClassification Report:")
print(classification_report(y_test, y_pred_classes, target_names=le.classes_))

# Tahminlerin dağılımını görme
predictions = le.inverse_transform(y_pred_classes)
pred_distribution = pd.Series(predictions).value_counts()
total_predictions = len(predictions)

print("\nTeknisyen Tahmin Dağılımı:")
for teknisyen, count in pred_distribution.items():
    percentage = (count/total_predictions) * 100
    print(f"{teknisyen}: {count} tahmin (%{percentage:.2f})")

# Gerçek dağılımlar vs Model tahminleri analizi
print("\nGerçek Dağılımlar vs Model Tahminleri:")

# 1. Teknisyen dağılımı (mevcut kod)
print("\nGerçek Dağılım (SQL'den):")
print("Zeynep Aksoy: %12.57")
print("Murat Aydın: %12.52")
print("Ahmet Yılmaz: %12.51")
print("Fatma Şahin: %12.51")
print("Ali Öztürk: %12.48")
print("Ayşe Kaya: %12.48")
print("Mehmet Demir: %12.47")
print("Can Yıldız: %12.46")

# 2. Model tahminleri
print("\nModel Tahminleri:")
predictions = le.inverse_transform(y_pred_classes)
tahmin_dagilim = pd.Series(predictions).value_counts(normalize=True) * 100
print(tahmin_dagilim)

# Test verisini DataFrame'e çevirelim
test_df = pd.DataFrame({
    'Teknisyen': le.inverse_transform(y_test.astype(int)),
    'Tahmin': predictions,
    'Kategori': df['Kategori'].iloc[len(df)-len(y_test):].values,
    'Oncelik': df['Oncelik'].iloc[len(df)-len(y_test):].values
})

# Kategori analizi
print("\nKategori Bazlı Tahmin Dağılımı:")
for kategori in ['Donanım', 'Güvenlik', 'Ağ', 'Veritabanı', 'Yazılım']:
    print(f"\n{kategori} kategorisinde:")
    mask = test_df['Kategori'] == kategori
    kategori_tahminleri = test_df[mask]['Tahmin']
    kategori_dagilim = pd.Series(kategori_tahminleri).value_counts(normalize=True) * 100
    print(kategori_dagilim)

# Öncelik analizi
print("\nÖncelik Bazlı Tahmin Dağılımı:")
for oncelik in ['Düşük', 'Yüksek', 'Orta']:
    print(f"\n{oncelik} öncelikli işlerde:")
    mask = test_df['Oncelik'] == oncelik
    oncelik_tahminleri = test_df[mask]['Tahmin']
    oncelik_dagilim = pd.Series(oncelik_tahminleri).value_counts(normalize=True) * 100
    print(oncelik_dagilim)
