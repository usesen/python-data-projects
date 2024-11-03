import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# SQL bağlantısı
engine = create_engine('mssql+pyodbc://usesen:usesen@DESKTOP-6QR83E3\\UGURMSSQL/FSM_Tickets?driver=SQL+Server')

# 1. Genel Ticket Sayısı Tahmini
query_total = """
SELECT 
    CAST(Olusturma_Tarihi AS DATE) as Tarih,
    COUNT(*) as Ticket_Sayisi
FROM Tickets
GROUP BY CAST(Olusturma_Tarihi AS DATE)
ORDER BY Tarih
"""
df_total = pd.read_sql(query_total, engine)

# Holt-Winters modelini uygula
model_hw = ExponentialSmoothing(
    df_total['Ticket_Sayisi'],
    seasonal_periods=7,  # Haftalık sezonsellik
    trend='add',
    seasonal='add'
).fit()

# Gelecek 270 gün için tahmin (9 ay)
forecast_hw = model_hw.forecast(270)

# 2. Bölge ve Kategori Bazlı Tahmin
query_detailed = """
SELECT 
    CAST(Olusturma_Tarihi AS DATE) as Tarih,
    Bolge,
    Kategori,
    Alt_Kategori,
    COUNT(*) as Ticket_Sayisi,
    DATEPART(dw, Olusturma_Tarihi) as Haftanin_Gunu,
    DATEPART(month, Olusturma_Tarihi) as Ay,
    DATEPART(hour, Olusturma_Tarihi) as Saat,
    Is_Gununde_mi,
    Mesai_Saatinde_mi,
    AVG(CAST(Musteri_Memnuniyeti as float)) as Ort_Memnuniyet
FROM Tickets
GROUP BY 
    CAST(Olusturma_Tarihi AS DATE),
    Bolge,
    Kategori,
    Alt_Kategori,
    DATEPART(dw, Olusturma_Tarihi),
    DATEPART(month, Olusturma_Tarihi),
    DATEPART(hour, Olusturma_Tarihi),
    Is_Gununde_mi,
    Mesai_Saatinde_mi
ORDER BY Tarih
"""
df_detailed = pd.read_sql(query_detailed, engine)

# Feature engineering
df_detailed['Tarih_Numeric'] = (df_detailed['Tarih'] - df_detailed['Tarih'].min()).dt.days

# Kategorik değişkenleri dönüştür
df_encoded = pd.get_dummies(df_detailed, columns=['Bolge', 'Kategori'])

# Features ve target
X = df_encoded.drop(['Tarih', 'Ticket_Sayisi'], axis=1)
y = df_encoded['Ticket_Sayisi']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Random Forest model
rf_model = RandomForestRegressor(
    n_estimators=200,
    max_depth=10,
    min_samples_split=5,
    random_state=42
)
rf_model.fit(X_train, y_train)

# Model performansı
y_pred = rf_model.predict(X_test)
print("\nModel Performansı:")
print(f"MAE: {mean_absolute_error(y_test, y_pred):.2f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_test, y_pred)):.2f}")
print(f"R2 Score: {r2_score(y_test, y_pred):.2f}")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nÖnemli Faktörler:")
print(feature_importance.head(10))

# Sonuçları görselleştir
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Genel Ticket Tahmini', 'Model Performansı', 
                   'Önemli Faktörler', 'Bölge-Kategori Tahminleri')
)

# 1. Genel tahmin grafiği
fig.add_trace(
    go.Scatter(x=df_total['Tarih'], y=df_total['Ticket_Sayisi'], 
               name='Gerçek Değerler'),
    row=1, col=1
)
fig.add_trace(
    go.Scatter(x=pd.date_range(start=df_total['Tarih'].max(), 
               periods=271)[1:],
               y=forecast_hw,
               name='Tahmin'),
    row=1, col=1
)

# 2. Model performans grafiği
fig.add_trace(
    go.Scatter(x=y_test.index, y=y_test, 
               name='Gerçek Test Değerleri'),
    row=1, col=2
)
fig.add_trace(
    go.Scatter(x=y_test.index, y=y_pred, 
               name='Tahmin Edilen Değerler'),
    row=1, col=2
)

# 3. Feature importance grafiği
fig.add_trace(
    go.Bar(x=feature_importance['feature'][:10], 
           y=feature_importance['importance'][:10],
           name='Önem Derecesi'),
    row=2, col=1
)

fig.update_layout(height=1000, width=1500, title_text="Ticket Tahmin Analizi")
fig.show() 