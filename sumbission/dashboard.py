import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# ======================================
# Konfigurasi Halaman
# ======================================
st.set_page_config(
    page_title="Dashboard Analisis E-Commerce",
    layout="wide"
)

st.title("Dashboard Analisis Data E-Commerce")

st.write("""
Dashboard ini menampilkan analisis data e-commerce berdasarkan:
1. Kategori produk dengan revenue terbesar
2. Segmentasi pelanggan berdasarkan nilai transaksi (Monetary)
""")

# ======================================
# Load Data
# ======================================
df = pd.read_csv("main_data.csv")
# Konversi tanggal
df["order_purchase_timestamp"] = pd.to_datetime(
    df["order_purchase_timestamp"]
)

# ======================================
# Sidebar Filter (FITUR INTERAKTIF)
# ======================================
st.sidebar.header("Filter Data")

# Filter kategori produk
category = st.sidebar.selectbox(
    "Pilih Kategori Produk",
    options=["Semua"] + sorted(
        df["product_category_name"].dropna().unique().tolist()
    )
)

# Filter state pelanggan
state = st.sidebar.selectbox(
    "Pilih State Pelanggan",
    options=["Semua"] + sorted(
        df["customer_state"].dropna().unique().tolist()
    )
)

# ======================================
# Filtering Data
# ======================================
filtered_df = df.copy()

if category != "Semua":
    filtered_df = filtered_df[
        filtered_df["product_category_name"] == category
    ]

if state != "Semua":
    filtered_df = filtered_df[
        filtered_df["customer_state"] == state
    ]

# ======================================
# KPI
# ======================================
st.subheader("Ringkasan Data")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Revenue",
    f"{filtered_df['price'].sum():,.0f}"
)

col2.metric(
    "Total Order",
    filtered_df["order_id"].nunique()
)

col3.metric(
    "Total Customer",
    filtered_df["customer_unique_id"].nunique()
)

# ======================================
# VISUALISASI 1
# Top Kategori Revenue
# ======================================
st.subheader("Top 10 Kategori Berdasarkan Revenue")

top_category = (
    filtered_df.groupby("product_category_name")["price"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

fig, ax = plt.subplots(figsize=(10,5))

sns.barplot(
    x=top_category.values,
    y=top_category.index,
    ax=ax
)

ax.set_title("Top 10 Kategori Berdasarkan Revenue")
ax.set_xlabel("Revenue")
ax.set_ylabel("Kategori Produk")

st.pyplot(fig)

# ======================================
# VISUALISASI 2
# Distribusi Monetary
# ======================================
st.subheader("Distribusi Monetary Pelanggan")

snapshot_date = (
    filtered_df["order_purchase_timestamp"].max()
    + pd.Timedelta(days=1)
)

rfm = filtered_df.groupby("customer_unique_id").agg({
    "order_purchase_timestamp": lambda x:
        (snapshot_date - x.max()).days,
    "order_id": "nunique",
    "price": "sum"
})

rfm.columns = ["Recency", "Frequency", "Monetary"]

fig, ax = plt.subplots(figsize=(10,5))

sns.histplot(
    rfm["Monetary"],
    bins=30,
    kde=True,
    ax=ax
)

ax.set_title("Distribusi Monetary Pelanggan")
ax.set_xlabel("Monetary")
ax.set_ylabel("Jumlah Pelanggan")

st.pyplot(fig)

# ======================================
# Insight
# ======================================
st.subheader("Insight")

if not top_category.empty:

    best_category = top_category.index[0]
    best_revenue = top_category.iloc[0]

    st.write(f"""
    - Kategori produk dengan revenue terbesar adalah **{best_category}**
    dengan total revenue sebesar **{best_revenue:,.0f}**.

    - Distribusi Monetary menunjukkan bahwa sebagian besar pelanggan
    memiliki nilai transaksi rendah hingga menengah, namun terdapat
    sejumlah kecil pelanggan dengan nilai transaksi tinggi.

    - Dashboard memiliki fitur interaktif berupa filter kategori produk
    dan state pelanggan yang memengaruhi seluruh visualisasi.
    """)

else:
    st.warning(
        "Tidak ada data yang sesuai dengan filter yang dipilih."
    )
