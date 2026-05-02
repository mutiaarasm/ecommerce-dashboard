import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# ===== Title =====
st.title("Dashboard Analisis Data E-Commerce")

# ===== Load Data =====
df = pd.read_csv("main_data.csv")

# ===== Preview Data =====
st.subheader("Preview Data")
st.dataframe(df.head())

# ===== Analisis 1 =====
st.subheader("Top 10 Kategori Berdasarkan Revenue")

top_category = df.groupby("product_category_name")["price"].sum().sort_values(ascending=False).head(10)

fig, ax = plt.subplots(figsize=(10,5))
top_category.plot(kind='bar', ax=ax)
ax.set_title("Top 10 Kategori Berdasarkan Revenue")
ax.set_xlabel("Kategori Produk")
ax.set_ylabel("Revenue")
plt.xticks(rotation=45)

st.pyplot(fig)

# ===== Analisis 2 (RFM) =====
st.subheader("Distribusi Monetary Pelanggan")

df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])

snapshot_date = df['order_purchase_timestamp'].max() + pd.Timedelta(days=1)

rfm = df.groupby('customer_id').agg({
    'order_purchase_timestamp': lambda x: (snapshot_date - x.max()).days,
    'customer_id': 'count',
    'price': 'sum'
})

rfm.columns = ['Recency', 'Frequency', 'Monetary']

fig, ax = plt.subplots(figsize=(10,5))
sns.histplot(rfm['Monetary'], ax=ax)
ax.set_title("Distribusi Monetary")
ax.set_xlabel("Monetary")
ax.set_ylabel("Jumlah Pelanggan")

st.pyplot(fig)

# ===== Insight =====
st.subheader("Insight")

st.write("""
- Kategori 'beleza_saude' memiliki kontribusi revenue terbesar.
- Sebagian besar pelanggan memiliki nilai transaksi rendah.
- Terdapat kelompok kecil pelanggan dengan nilai transaksi tinggi yang berkontribusi besar terhadap revenue.
""")