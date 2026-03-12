import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# --- 1. AYARLAR & MASTER DATA ---
years = [2024, 2025, 2026]
global_end_date = datetime(2026, 3, 11)

channels = ['Zincir Market', 'Tekel Bayi', 'Meyhane/Restoran', 'Horeca (Otel)']
chains = ['Migros', 'Macrocenter', 'CarrefourSA', 'Metro', 'A101']

regions_data = {
    'Marmara': ['İstanbul', 'Bursa', 'Kocaeli', 'Tekirdağ', 'Edirne'],
    'Ege': ['İzmir', 'Muğla', 'Aydın', 'Manisa'],
    'İç Anadolu': ['Ankara', 'Eskişehir', 'Konya'],
    'Akdeniz': ['Antalya', 'Adana', 'Mersin'],
    'Karadeniz': ['Samsun', 'Trabzon']
}

# --- 2. MASTER TABLOLARIN OLUŞTURULMASI ---
city_rows = []
city_id = 1
for reg, cities in regions_data.items():
    for city in cities:
        city_rows.append({'Sehir_ID': city_id, 'Sehir_Adi': city, 'Bolge_Adi': reg})
        city_id += 1
df_cities = pd.DataFrame(city_rows)

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

# --- 3. SATIŞ NOKTALARI ---
points = []
for i in range(1, 151):
    channel = random.choice(channels)
    city_row = df_cities.sample(1).iloc[0]
    chain_name = random.choice(chains) if channel == 'Zincir Market' else 'Bağımsız'
    
    frekans = random.uniform(0.1, 0.45) 
    hacim_carpani = random.uniform(0.5, 4.0) 
    
    if random.random() > 0.35:
        p_last_date = global_end_date - timedelta(days=random.randint(0, 4))
    else:
        p_last_date = global_end_date - timedelta(days=random.randint(15, 150))

    points.append({
        'Nokta_ID': 5000 + i,
        'Nokta_Adi': f"{chain_name} - Bayi {i}" if chain_name != 'Bağımsız' else f"Nokta {i} ({channel})",
        'Kanal': channel,
        'Zincir_Adi': chain_name,
        'Sehir_ID': city_row['Sehir_ID'],
        'Frekans': frekans,
        'Hacim': hacim_carpani,
        'Son_Alim_Tarihi': p_last_date
    })
df_points = pd.DataFrame(points)

# --- 4. FİYAT LİSTESİ ---
price_rows = []
for idx, row in df_products.iterrows():
    base = (row['Hacim_cl'] * 25) if 'Göbek' in row['Seri'] else (row['Hacim_cl'] * 18)
    price_rows.append({'Urun_ID': row['Urun_ID'], 'Tarih': '2024-01-01', 'Birim_Fiyat': base})
    price_rows.append({'Urun_ID': row['Urun_ID'], 'Tarih': '2025-01-01', 'Birim_Fiyat': base * 1.60})
    price_rows.append({'Urun_ID': row['Urun_ID'], 'Tarih': '2026-01-01', 'Birim_Fiyat': base * 2.15})
df_prices = pd.DataFrame(price_rows)
df_prices['Tarih'] = pd.to_datetime(df_prices['Tarih'])

# --- 5. SATIŞ ÜRETİMİ (KESİN 11 MART LİMİTİ) ---
sales_data = []
start_dt = datetime(2024, 1, 1)

for _, pt in df_points.iterrows():
    curr = start_dt
    limit = pt['Son_Alim_Tarihi']
    while curr <= limit:
        is_deadline = (curr.date() == global_end_date.date() and limit.date() == global_end_date.date())
        if random.random() < pt['Frekans'] or is_deadline:
            num_items = random.randint(1, int(2 + pt['Hacim']))
            for _ in range(num_items):
                prod = df_products.sample(1, weights=df_products['Satis_Agirligi']).iloc[0]
                base_q = random.choices([1, 6, 12, 24], weights=[60, 25, 10, 5])[0]
                qty = max(1, int(base_q * pt['Hacim']))
                sales_data.append({
                    'Satis_ID': len(sales_data) + 1,
                    'Tarih': curr + timedelta(hours=random.randint(9, 21)),
                    'Nokta_ID': pt['Nokta_ID'],
                    'Urun_ID': prod['Urun_ID'],
                    'Miktar_Adet': qty,
                    'Toplam_Litre': qty * prod['Hacim_L']
                })
        curr += timedelta(days=1)

df_sales = pd.DataFrame(sales_data)

# --- 6. FİNANSAL TABLO ---
def calc_fin(row):
    p_match = df_prices[(df_prices['Urun_ID'] == row['Urun_ID']) & (df_prices['Tarih'] <= row['Tarih'])]
    unit_p = p_match['Birim_Fiyat'].iloc[-1]
    brut = unit_p * row['Miktar_Adet']
    isk = brut * random.uniform(0.05, 0.15)
    net = brut - isk
    return pd.Series([brut, isk, net, net*0.42, net*0.18, net*0.15, net*0.08, net*0.17])

df_sales_fin = df_sales[['Satis_ID']].copy()
df_sales_fin[['Brut_Ciro', 'Iskonto', 'Net_Satis', 'OTV', 'KDV', 'COGS', 'OPEX', 'EBIT']] = df_sales.apply(calc_fin, axis=1)

# --- 7. MANTIKLI BÜTÇE HEDEFLERİ (SATIŞ BAZLI) ---
# Gerçekleşen satışları ay ve ürün bazında özetleyelim
df_sales['Ay_Yil'] = df_sales['Tarih'].dt.to_period('M').dt.to_timestamp()
actual_summary = df_sales.groupby(['Ay_Yil', 'Urun_ID'])['Miktar_Adet'].sum().reset_index()

budget_rows = []
for yr in years:
    max_m = 13 if yr < 2026 else 4
    for month in range(1, max_m):
        donem = datetime(yr, month, 1)
        for _, p in df_products.iterrows():
            # Bu ürün ve bu ay için gerçek satış var mı?
            actual_val = actual_summary[(actual_summary['Ay_Yil'] == donem) & (actual_summary['Urun_ID'] == p['Urun_ID'])]
            
            if not actual_val.empty:
                ref_qty = actual_val['Miktar_Adet'].values[0]
            else:
                # Satış olmayan aylar için (örn 2026 Mart sonu) bir tahmin yap
                ref_qty = random.randint(100, 300)

            # Hedef: Gerçek satışın %80 ile %120'si arasında olsun (Bazı aylar geçsin, bazıları kalsın)
            target_qty = int(ref_qty * random.uniform(0.8, 1.25))
            
            # Finansal hedefleri de buna göre ölçekle (Net Satis birim fiyati yaklasik 1500 kabul edildi)
            budget_rows.append({
                'Donem': donem,
                'Urun_ID': p['Urun_ID'],
                'Hedef_Adet': target_qty,
                'Hedef_Litre': target_qty * p['Hacim_L'],
                'Hedef_Net_Satis': target_qty * 1400,
                'Hedef_EBIT': target_qty * 220,
                'Hedef_COGS': target_qty * 280,
                'Hedef_OPEX': target_qty * 130
            })
df_budget = pd.DataFrame(budget_rows)

# --- 8. KAYIT VE TEMİZLİK ---
df_sales.drop(columns=['Ay_Yil']).to_csv('Satis.csv', index=False)
df_products.to_csv('Urunler_Master.csv', index=False)
df_points.drop(columns=['Frekans', 'Hacim']).to_csv('Satis_Noktalari_Master.csv', index=False)
df_sales_fin.to_csv('Satis_Finansal.csv', index=False)
df_budget.to_csv('Butce_Genel.csv', index=False)
df_cities.to_csv('Sehirler.csv', index=False)
df_prices.to_csv('Fiyat_Tarihleri.csv', index=False)

print(f"Sistem hazır! Son Satış: {df_sales['Tarih'].max()}")