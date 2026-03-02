import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# --- AYARLAR & MASTER DATA ---
years = [2024, 2025, 2026]
channels = ['Zincir Market', 'Tekel Bayi', 'Meyhane/Restoran', 'Horeca (Otel)']
chains = ['Migros', 'Macrocenter', 'CarrefourSA', 'Metro', 'A101']

# 1. Bölgeler ve Şehirler
regions_data = {
    'Marmara': ['İstanbul', 'Bursa', 'Kocaeli', 'Tekirdağ'],
    'Ege': ['İzmir', 'Muğla', 'Aydın', 'Manisa'],
    'İç Anadolu': ['Ankara', 'Eskişehir', 'Konya'],
    'Akdeniz': ['Antalya', 'Adana', 'Mersin'],
    'Karadeniz': ['Samsun', 'Trabzon']
}

city_rows = []
city_id = 1
for reg, cities in regions_data.items():
    for city in cities:
        city_rows.append({'Sehir_ID': city_id, 'Sehir_Adi': city, 'Bolge_Adi': reg})
        city_id += 1
df_cities = pd.DataFrame(city_rows)

# 2. Ürünler Master (Tüm Boylar & Seriler)
series = {
    'Göbek': {'weights': 0.45, 'cl': [20, 35, 50, 70, 100]},
    'Mavi Seri': {'weights': 0.30, 'cl': [20, 35, 50, 70, 100]},
    'Teruar': {'weights': 0.05, 'cl': [70]},
    'Razaki': {'weights': 0.05, 'cl': [70]},
    'Kalecik Karası': {'weights': 0.05, 'cl': [70]},
    'Yaş Üzüm': {'weights': 0.05, 'cl': [35, 70, 100]},
    'İncir': {'weights': 0.03, 'cl': [70]},
    'Kampanya Paketi (2 Bardak Hediye)': {'weights': 0.02, 'cl': [70]}
}

product_rows = []
p_id = 1001
for s_name, details in series.items():
    for size in details['cl']:
        product_rows.append({
            'Urun_ID': p_id,
            'Barkod': f"869{random.randint(100000, 999999)}",
            'Urun_Adi': f"Beylerbeyi {s_name} {size}cl",
            'Seri': s_name,
            'Hacim_cl': size,
            'Hacim_L': size / 100,
            'Urun_Tipi': 'Standart' if 'Kampanya' not in s_name else 'Promosyon',
            'Satis_Agirligi': details['weights'] / len(details['cl'])
        })
        p_id += 1
df_products = pd.DataFrame(product_rows)

# 3. Satış Noktaları Master (Customer Master)
points = []
for i in range(1, 151): # 150 Nokta
    channel = random.choice(channels)
    city_row = df_cities.sample(1).iloc[0]
    chain_name = random.choice(chains) if channel == 'Zincir Market' else 'Bağımsız'
    points.append({
        'Nokta_ID': 5000 + i,
        'Nokta_Adi': f"{chain_name} - Bayi {i}" if chain_name != 'Bağımsız' else f"Nokta {i} ({channel})",
        'Kanal': channel,
        'Zincir_Adi': chain_name,
        'Sehir_ID': city_row['Sehir_ID']
    })
df_points = pd.DataFrame(points)

# 4. Fiyat Tarihleri (Enflasyonist Geçişler)
price_rows = []
for idx, row in df_products.iterrows():
    base = (row['Hacim_cl'] * 15) if 'Göbek' in row['Seri'] else (row['Hacim_cl'] * 11)
    price_rows.append({'Urun_ID': row['Urun_ID'], 'Tarih': '2024-01-01', 'Birim_Fiyat': base})
    price_rows.append({'Urun_ID': row['Urun_ID'], 'Tarih': '2025-01-01', 'Birim_Fiyat': base * 1.50})
    price_rows.append({'Urun_ID': row['Urun_ID'], 'Tarih': '2026-01-01', 'Birim_Fiyat': base * 1.85})
df_prices = pd.DataFrame(price_rows)
df_prices['Tarih'] = pd.to_datetime(df_prices['Tarih'])

# --- FACT TABLES GENERATION ---

sales_data = []
start_date = datetime(2024, 1, 1)
end_date = datetime(2026, 2, 28)

curr = start_date
while curr <= end_date:
    # Hafta sonu ve Özel gün çarpanı
    daily_multiplier = 1.5 if curr.weekday() >= 4 else 1.0
    num_sales = int(random.randint(40, 80) * daily_multiplier)
    
    for _ in range(num_sales):
        prod = df_products.sample(1, weights=df_products['Satis_Agirligi']).iloc[0]
        point = df_points.sample(1).iloc[0]
        qty = random.choice([1, 1, 1, 2, 6, 12]) # Genelde 1 adet, bazen koli
        
        sales_data.append({
            'Satis_ID': len(sales_data) + 1,
            'Tarih': curr,
            'Nokta_ID': point['Nokta_ID'],
            'Urun_ID': prod['Urun_ID'],
            'Miktar_Adet': qty,
            'Toplam_Litre': qty * prod['Hacim_L']
        })
    curr += timedelta(days=1)

df_sales = pd.DataFrame(sales_data)

# 5. Satış (Finansal) - Türkiye Vergi Mantığı
def calc_fin(row):
    price = df_prices[(df_prices['Urun_ID'] == row['Urun_ID']) & (df_prices['Tarih'] <= row['Tarih'])]['Birim_Fiyat'].iloc[-1]
    brut_ciro = price * row['Miktar_Adet']
    iskonto = brut_ciro * random.uniform(0.05, 0.12)
    net_satis = brut_ciro - iskonto
    # Türkiye Alkol Vergisi Simülasyonu
    otv = net_satis * 0.62 
    kdv = (net_satis) * 0.20
    cogs = (net_satis * 0.15) # Üretim maliyeti
    opex = net_satis * 0.10 # Lojistik + Pazarlama
    ebit = net_satis - (otv + kdv + cogs + opex)
    
    return pd.Series([brut_ciro, iskonto, net_satis, otv, kdv, cogs, opex, ebit])

financial_cols = ['Brut_Ciro', 'Iskonto', 'Net_Satis', 'OTV', 'KDV', 'COGS', 'OPEX', 'EBIT']
df_sales_fin = df_sales.copy()
df_sales_fin[financial_cols] = df_sales.apply(calc_fin, axis=1)

# 6. Bütçe ve Bütçe Finansal (Aylık)
budget_rows = []
for yr in years:
    for month in range(1, 13):
        if yr == 2026 and month > 3: break
        for _, p in df_products.iterrows():
            target_qty = random.randint(200, 500)
            budget_rows.append({
                'Donem': datetime(yr, month, 1),
                'Urun_ID': p['Urun_ID'],
                'Hedef_Adet': target_qty,
                'Hedef_Litre': target_qty * p['Hacim_L'],
                'Hedef_Net_Satis': target_qty * 800, # Ortalama
                'Hedef_EBIT': target_qty * 150,
                'Hedef_COGS': target_qty * 120,
                'Hedef_OPEX': target_qty * 50
            })
df_budget = pd.DataFrame(budget_rows)

# Dosyaları Kaydet
df_sales.to_csv('Satis.csv', index=False)
df_products.to_csv('Urunler_Master.csv', index=False)
df_points.to_csv('Satis_Noktalari_Master.csv', index=False)
df_sales_fin.to_csv('Satis_Finansal.csv', index=False)
df_budget.to_csv('Butce_Genel.csv', index=False)
df_cities.to_csv('Sehirler.csv', index=False)
df_prices.to_csv('Fiyat_Tarihleri.csv', index=False)

print("Kanka tüm tablolar (Litre bazlı) hazır! Power BI seni bekler.")