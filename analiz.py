import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from sqlalchemy import create_engine

# SQL bağlantısı
engine = create_engine('mssql+pyodbc://usesen:usesen@DESKTOP-6QR83E3\\UGURMSSQL/FSM_Tickets?driver=SQL+Server')

# Veriyi çek
query = """
SELECT 
    CAST(Olusturma_Tarihi AS DATE) as Tarih,
    Bolge,
    Kategori,
    Alt_Kategori,
    Is_Gununde_mi,
    Mesai_Saatinde_mi,
    COUNT(*) as Ticket_Sayisi
FROM Tickets
GROUP BY 
    CAST(Olusturma_Tarihi AS DATE),
    Bolge,
    Kategori,
    Alt_Kategori,
    Is_Gununde_mi,
    Mesai_Saatinde_mi
ORDER BY 
    Tarih
"""

df = pd.read_sql(query, engine)

# Tek bir figure'da tüm grafikleri oluştur
fig = make_subplots(
    rows=3, cols=2,
    subplot_titles=(
        'Günlük Ticket Sayısı Trendi', 
        'Bölge Bazlı Ticket Dağılımı',
        'Kategori Bazlı Ticket Trendi', 
        'İş Günü vs Hafta Sonu Analizi',
        'Bölge-Kategori Ticket Dağılımı'
    ),
    specs=[[{"type": "scatter"}, {"type": "bar"}],
           [{"type": "scatter"}, {"type": "bar"}],
           [{"type": "heatmap"}, None]],
    vertical_spacing=0.12,
    horizontal_spacing=0.1
)

# 1. Günlük Ticket Trendi
daily_tickets = df.groupby('Tarih')['Ticket_Sayisi'].sum().reset_index()
fig.add_trace(
    go.Scatter(x=daily_tickets['Tarih'], y=daily_tickets['Ticket_Sayisi'],
               name="Günlük Trend"),
    row=1, col=1
)

# 2. Bölge Bazlı Dağılım
region_dist = df.groupby('Bolge')['Ticket_Sayisi'].sum().reset_index()
fig.add_trace(
    go.Bar(x=region_dist['Bolge'], y=region_dist['Ticket_Sayisi'],
           name="Bölge Dağılımı"),
    row=1, col=2
)

# 3. Kategori Trendi
category_trend = df.pivot_table(
    index='Tarih',
    columns='Kategori',
    values='Ticket_Sayisi',
    aggfunc='sum'
).reset_index()

for column in category_trend.columns:
    if column != 'Tarih':
        fig.add_trace(
            go.Scatter(x=category_trend['Tarih'], 
                      y=category_trend[column],
                      name=column),
            row=2, col=1
        )

# 4. İş Günü Analizi
work_day_analysis = df.groupby('Is_Gununde_mi')['Ticket_Sayisi'].mean().reset_index()
work_day_analysis['Is_Gununde_mi'] = work_day_analysis['Is_Gununde_mi'].map(
    {1: 'İş Günü', 0: 'Hafta Sonu'}
)
fig.add_trace(
    go.Bar(x=work_day_analysis['Is_Gununde_mi'], 
           y=work_day_analysis['Ticket_Sayisi'],
           name="İş Günü Analizi"),
    row=2, col=2
)

# 5. Heatmap
heatmap_data = df.pivot_table(
    index='Bolge',
    columns='Kategori',
    values='Ticket_Sayisi',
    aggfunc='sum'
)
fig.add_trace(
    go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='YlOrRd',
        name="Heatmap"
    ),
    row=3, col=1
)

# Layout düzenlemeleri
fig.update_layout(
    height=1200,
    width=1600,
    title_text="Ticket Analiz Dashboard'u",
    showlegend=True,
    template='plotly_white'
)

# X ekseni başlıkları
fig.update_xaxes(title_text="Tarih", row=1, col=1)
fig.update_xaxes(title_text="Bölge", row=1, col=2)
fig.update_xaxes(title_text="Tarih", row=2, col=1)
fig.update_xaxes(title_text="", row=2, col=2)
fig.update_xaxes(title_text="Kategori", row=3, col=1)

# Y ekseni başlıkları
fig.update_yaxes(title_text="Ticket Sayısı", row=1, col=1)
fig.update_yaxes(title_text="Ticket Sayısı", row=1, col=2)
fig.update_yaxes(title_text="Ticket Sayısı", row=2, col=1)
fig.update_yaxes(title_text="Ortalama Ticket", row=2, col=2)
fig.update_yaxes(title_text="Bölge", row=3, col=1)

fig.show() 