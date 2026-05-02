from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# =============================
# Konfigurasi Halaman
# =============================
st.set_page_config(
    page_title="Dashboard Analisis E-Commerce",
    page_icon="shopping_cart",
    layout="wide"
)

st.title("Dashboard Analisis Data E-Commerce")
st.write(
    "Dashboard ini menampilkan analisis revenue kategori produk dan segmentasi pelanggan "
    "berdasarkan nilai transaksi. Gunakan filter di sidebar untuk berinteraksi dengan visualisasi."
)

# =============================
# Load Data
# =============================
@st.cache_data
def load_data():
    possible_paths = [
        Path("dashboard/main_data.csv"),
        Path("main_data.csv"),
        Path(__file__).resolve().parent / "main_data.csv",
        Path(__file__).resolve().parent / "dashboard" / "main_data.csv",
    ]

    data_path = None
    for path in possible_paths:
        if path.exists():
            data_path = path
            break

    if data_path is None:
        st.error(
            "File main_data.csv tidak ditemukan. Pastikan file berada di folder dashboard/ "
            "atau folder yang sama dengan dashboard.py."
        )
        st.stop()

    data = pd.read_csv(data_path)
    data["order_purchase_timestamp"] = pd.to_datetime(
        data["order_purchase_timestamp"], errors="coerce"
    )
    data = data.dropna(subset=["order_purchase_timestamp", "price"])
    data["order_date"] = data["order_purchase_timestamp"].dt.date
    return data


df = load_data()

# =============================
# Sidebar Filter Interaktif
# =============================
st.sidebar.header("Filter Data")

min_date = df["order_purchase_timestamp"].min().date()
max_date = df["order_purchase_timestamp"].max().date()

st.sidebar.caption(
    f"Rentang tanggal dataset: {min_date.strftime('%Y/%m/%d')} - {max_date.strftime('%Y/%m/%d')}"
)

# Key baru agar Streamlit tidak memakai cache pilihan tanggal lama yang invalid.
date_range = st.sidebar.date_input(
    "Rentang Tanggal Pembelian",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="valid_order_date_range_v2",
)

# Antisipasi jika user baru memilih satu tanggal.
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

if start_date > end_date:
    st.sidebar.error("Tanggal mulai tidak boleh lebih besar dari tanggal akhir.")
    st.stop()

category_options = sorted(df["product_category_name"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Kategori Produk",
    options=category_options,
    default=category_options,
)

state_options = sorted(df["customer_state"].dropna().unique())
selected_states = st.sidebar.multiselect(
    "State Pelanggan",
    options=state_options,
    default=state_options,
)

filtered_df = df[
    (df["order_date"] >= start_date)
    & (df["order_date"] <= end_date)
    & (df["product_category_name"].isin(selected_categories))
    & (df["customer_state"].isin(selected_states))
].copy()

if filtered_df.empty:
    st.warning("Tidak ada data untuk kombinasi filter yang dipilih. Silakan ubah filter.")
    st.stop()

# =============================
# KPI
# =============================
st.subheader("Ringkasan Data Terfilter")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"{filtered_df['price'].sum():,.0f}")
col2.metric("Total Order", f"{filtered_df['order_id'].nunique():,}")
col3.metric("Total Pelanggan", f"{filtered_df['customer_unique_id'].nunique():,}")
col4.metric("Rata-rata Harga", f"{filtered_df['price'].mean():,.2f}")

# =============================
# Preview Data
# =============================
with st.expander("Lihat Preview Data"):
    st.dataframe(filtered_df.head(20))

# =============================
# Analisis 1: Revenue Kategori
# =============================
st.subheader("Top 10 Kategori Berdasarkan Revenue")

top_category = (
    filtered_df.groupby("product_category_name")["price"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(x=top_category.values, y=top_category.index, ax=ax)
ax.set_title("Top 10 Kategori Berdasarkan Revenue")
ax.set_xlabel("Revenue")
ax.set_ylabel("Kategori Produk")
st.pyplot(fig)

# =============================
# Tren Revenue Bulanan
# =============================
st.subheader("Tren Revenue Bulanan")

monthly_revenue = (
    filtered_df.set_index("order_purchase_timestamp")
    .resample("ME")["price"]
    .sum()
    .reset_index()
)

fig, ax = plt.subplots(figsize=(10, 5))
sns.lineplot(data=monthly_revenue, x="order_purchase_timestamp", y="price", marker="o", ax=ax)
ax.set_title("Tren Revenue Bulanan")
ax.set_xlabel("Bulan")
ax.set_ylabel("Revenue")
plt.xticks(rotation=45)
st.pyplot(fig)

# =============================
# Analisis 2: RFM Monetary
# =============================
st.subheader("Distribusi Monetary Pelanggan")

snapshot_date = filtered_df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

rfm = filtered_df.groupby("customer_unique_id").agg({
    "order_purchase_timestamp": lambda x: (snapshot_date - x.max()).days,
    "order_id": "nunique",
    "price": "sum",
})

rfm.columns = ["Recency", "Frequency", "Monetary"]

fig, ax = plt.subplots(figsize=(10, 5))
sns.histplot(rfm["Monetary"], bins=40, kde=True, ax=ax)
ax.set_title("Distribusi Monetary Pelanggan")
ax.set_xlabel("Monetary")
ax.set_ylabel("Jumlah Pelanggan")
st.pyplot(fig)

# Segmentasi sederhana Monetary
st.subheader("Segmentasi Pelanggan Berdasarkan Monetary")

if rfm["Monetary"].nunique() >= 3 and len(rfm) >= 3:
    rfm["Monetary Segment"] = pd.qcut(
        rfm["Monetary"].rank(method="first"),
        q=3,
        labels=["Low Value", "Medium Value", "High Value"]
    )
else:
    rfm["Monetary Segment"] = "All Customers"

segment_summary = rfm.groupby("Monetary Segment", observed=False).agg({
    "Monetary": ["count", "mean", "sum"],
    "Frequency": "mean",
    "Recency": "mean",
})

st.dataframe(segment_summary)

fig, ax = plt.subplots(figsize=(8, 5))
segment_revenue = (
    rfm.groupby("Monetary Segment", observed=False)["Monetary"]
    .sum()
    .sort_values(ascending=False)
)
sns.barplot(x=segment_revenue.index.astype(str), y=segment_revenue.values, ax=ax)
ax.set_title("Revenue Berdasarkan Segmentasi Monetary")
ax.set_xlabel("Segmentasi")
ax.set_ylabel("Total Monetary")
st.pyplot(fig)

# =============================
# Insight
# =============================
st.subheader("Insight")

best_category = top_category.index[0]
best_revenue = top_category.iloc[0]
high_value_revenue = segment_revenue.get("High Value", 0)
total_monetary = rfm["Monetary"].sum()
high_value_contribution = (high_value_revenue / total_monetary * 100) if total_monetary > 0 else 0

st.write(f"""
- Berdasarkan filter yang dipilih, kategori **{best_category}** menjadi kontributor revenue terbesar dengan total revenue **{best_revenue:,.0f}**.
- Distribusi Monetary pelanggan cenderung tidak merata: mayoritas pelanggan memiliki nilai transaksi rendah hingga menengah, sedangkan sebagian kecil pelanggan memiliki nilai transaksi tinggi.
- Segmen **High Value** berkontribusi sekitar **{high_value_contribution:.2f}%** terhadap total Monetary pada data terfilter.
- Filter tanggal, kategori produk, dan state pelanggan pada sidebar memengaruhi seluruh KPI dan visualisasi sehingga dashboard memenuhi unsur interaktif.
""")
