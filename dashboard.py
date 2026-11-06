from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

sns.set_theme(style="whitegrid")
BASE = Path(__file__).parent

SEASON_ORDER = ["Spring", "Summer", "Fall", "Winter"]
WEATHER_ORDER = [
    "Clear/Partly Cloudy",
    "Misty/Cloudy",
    "Light Snow/Rain",
    "Heavy Rain/Ice Pallets",
]
TIME_ORDER = [
    "Morning Rush Hour (06:00-09:59)",
    "Midday Leisure (10:00-15:59)",
    "Evening Rush Hour (16:00-19:59)",
    "Night/Early Morning (20:00-05:59)",
]

st.set_page_config(page_title="Bike Sharing Dashboard", page_icon="🚲", layout="wide")


SEASON_MAP = {1: "Spring", 2: "Summer", 3: "Fall", 4: "Winter"}
WEATHER_MAP = {
    1: "Clear/Partly Cloudy",
    2: "Misty/Cloudy",
    3: "Light Snow/Rain",
    4: "Heavy Rain/Ice Pallets",
}


def time_category(hour):
    if 6 <= hour < 10:
        return TIME_ORDER[0]
    if 10 <= hour < 16:
        return TIME_ORDER[1]
    if 16 <= hour < 20:
        return TIME_ORDER[2]
    return TIME_ORDER[3]


@st.cache_data
def load_data():
    """Gathering + Cleaning data (sama seperti di notebook).

    Membaca data/day.csv dan data/hour.csv, membersihkannya, lalu menyimpan
    hasilnya ke dashboard/day_data.csv dan dashboard/main_data.csv.
    Jika folder data/ tidak ada, dipakai CSV hasil olahan yang sudah tersimpan.
    """
    raw_day, raw_hour = BASE.parent / "data" / "day.csv", BASE.parent / "data" / "hour.csv"
    if raw_day.exists() and raw_hour.exists():
        day = pd.read_csv(raw_day)
        hour = pd.read_csv(raw_hour)
        for df in (day, hour):
            df["dteday"] = pd.to_datetime(df["dteday"])
            df["season_label"] = df["season"].map(SEASON_MAP)
            df["weather_label"] = df["weathersit"].map(WEATHER_MAP)
        hour["day_type"] = hour["workingday"].map({1: "Hari Kerja", 0: "Libur/Akhir Pekan"})
        hour["time_category"] = hour["hr"].apply(time_category)
        day.to_csv(BASE / "day_data.csv", index=False)
        hour.to_csv(BASE / "main_data.csv", index=False)
    else:
        day = pd.read_csv(BASE / "day_data.csv", parse_dates=["dteday"])
        hour = pd.read_csv(BASE / "main_data.csv", parse_dates=["dteday"])
    return day, hour


try:
    day_df, hour_df = load_data()
except FileNotFoundError:
    st.error(
        "Dataset tidak ditemukan. Letakkan day.csv dan hour.csv di folder `data/` "
        "(sejajar dengan folder `dashboard/`), lalu jalankan ulang dashboard."
    )
    st.stop()

# ---------------- Sidebar (filter) ----------------
with st.sidebar:
    st.title("🚲 Filter")
    min_date, max_date = day_df["dteday"].min().date(), day_df["dteday"].max().date()
    date_range = st.date_input(
        "Rentang tanggal", value=(min_date, max_date), min_value=min_date, max_value=max_date
    )
    seasons = st.multiselect(
        "Musim", SEASON_ORDER, default=SEASON_ORDER
    )
    weathers = st.multiselect(
        "Kondisi cuaca",
        [w for w in WEATHER_ORDER if w in day_df["weather_label"].unique()],
        default=[w for w in WEATHER_ORDER if w in day_df["weather_label"].unique()],
    )
    st.caption("Sumber data: Bike Sharing Dataset (2011-2012)")

if len(date_range) != 2:
    st.info("Pilih tanggal awal dan tanggal akhir pada filter di sidebar.")
    st.stop()

start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])


def apply_filters(df):
    return df[
        df["dteday"].between(start, end)
        & df["season_label"].isin(seasons)
        & df["weather_label"].isin(weathers)
    ]


day_f, hour_f = apply_filters(day_df), apply_filters(hour_df)

st.title("🚲 Bike Sharing Dashboard")
st.caption("Dashboard interaktif hasil analisis peminjaman sepeda 2011-2012")

if day_f.empty or hour_f.empty:
    st.warning("Tidak ada data untuk kombinasi filter ini. Ubah filter di sidebar.")
    st.stop()

# ---------------- KPI ----------------
c1, c2, c3 = st.columns(3)
c1.metric("Total Peminjaman", f"{day_f['cnt'].sum():,}")
c2.metric("Rata-rata per Hari", f"{day_f['cnt'].mean():,.0f}")
c3.metric("Jumlah Hari", f"{day_f['dteday'].nunique():,}")

tab1, tab2, tab3 = st.tabs(
    ["Pertanyaan 1: Cuaca & Musim", "Pertanyaan 2: Pola per Jam", "Analisis Lanjutan"]
)

# ---------------- Pertanyaan 1 ----------------
with tab1:
    st.subheader("Pengaruh cuaca dan musim terhadap rata-rata peminjaman harian")
    col_a, col_b = st.columns(2)

    season_avg = (
        day_f.groupby("season_label")["cnt"].mean().reindex(SEASON_ORDER).dropna().reset_index()
    )
    weather_avg = (
        day_f.groupby("weather_label")["cnt"].mean().reindex(WEATHER_ORDER).dropna().reset_index()
    )

    with col_a:
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.barplot(data=season_avg, x="season_label", y="cnt", hue="season_label",
                    palette="viridis", legend=False, ax=ax)
        ax.set_title("Rata-rata Peminjaman per Musim", fontweight="bold")
        ax.set_xlabel("Musim")
        ax.set_ylabel("Rata-rata peminjaman per hari")
        for p in ax.patches:
            ax.annotate(f"{p.get_height():,.0f}", (p.get_x() + p.get_width() / 2, p.get_height()),
                        ha="center", va="bottom", fontsize=9)
        st.pyplot(fig)

    with col_b:
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.barplot(data=weather_avg, x="weather_label", y="cnt", hue="weather_label",
                    palette="magma", legend=False, ax=ax)
        ax.set_title("Rata-rata Peminjaman per Kondisi Cuaca", fontweight="bold")
        ax.set_xlabel("Kondisi cuaca")
        ax.set_ylabel("Rata-rata peminjaman per hari")
        ax.tick_params(axis="x", rotation=15)
        for p in ax.patches:
            ax.annotate(f"{p.get_height():,.0f}", (p.get_x() + p.get_width() / 2, p.get_height()),
                        ha="center", va="bottom", fontsize=9)
        st.pyplot(fig)

    with st.expander("Lihat tabel musim × cuaca"):
        pivot = day_f.pivot_table(index="season_label", columns="weather_label",
                                  values="cnt", aggfunc="mean").round(0)
        st.dataframe(pivot)

    st.info(
        "**Kesimpulan:** Peminjaman tertinggi terjadi pada musim Fall, disusul Summer, "
        "dan terendah pada Spring. Cuaca cerah menghasilkan peminjaman tertinggi, "
        "sedangkan hujan/salju menurunkannya secara drastis."
    )

# ---------------- Pertanyaan 2 ----------------
with tab2:
    st.subheader("Pola peminjaman per jam: hari kerja vs libur/akhir pekan")
    hourly = hour_f.groupby(["day_type", "hr"])["cnt"].mean().reset_index()

    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(data=hourly, x="hr", y="cnt", hue="day_type", marker="o",
                 palette={"Hari Kerja": "#d62728", "Libur/Akhir Pekan": "#1f77b4"}, ax=ax)
    ax.set_title("Rata-rata Peminjaman per Jam", fontweight="bold")
    ax.set_xlabel("Jam (0-23)")
    ax.set_ylabel("Rata-rata peminjaman")
    ax.set_xticks(range(24))
    ax.legend(title="Jenis hari")
    ax.grid(True, linestyle="--", alpha=0.5)
    st.pyplot(fig)

    peaks = hourly.loc[hourly.groupby("day_type")["cnt"].idxmax()]
    cols = st.columns(len(peaks))
    for col, (_, row) in zip(cols, peaks.iterrows()):
        col.metric(f"Jam puncak: {row['day_type']}", f"{int(row['hr']):02d}:00",
                   f"{row['cnt']:.0f} peminjaman/jam", delta_color="off")

    st.info(
        "**Kesimpulan:** Hari kerja memiliki dua puncak tajam (sekitar 08:00 dan 17:00-18:00) "
        "akibat komuter, sedangkan hari libur berbentuk kurva landai dengan puncak sekitar 11:00-16:00."
    )

# ---------------- Analisis lanjutan ----------------
with tab3:
    st.subheader("Rata-rata peminjaman berdasarkan kategori waktu")
    tc = (
        hour_f.groupby("time_category")["cnt"].mean().reindex(TIME_ORDER).dropna()
        .sort_values(ascending=False).reset_index()
    )
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.barplot(data=tc, x="cnt", y="time_category", hue="time_category",
                palette="Blues_r", legend=False, ax=ax)
    ax.set_xlabel("Rata-rata peminjaman per jam")
    ax.set_ylabel("")
    for p in ax.patches:
        ax.annotate(f"{p.get_width():,.0f}", (p.get_width(), p.get_y() + p.get_height() / 2),
                    ha="left", va="center", fontsize=9)
    st.pyplot(fig)
    st.info(
        "**Rekomendasi:** (1) Pada hari kerja, pastikan stok sepeda melimpah di stasiun pemukiman "
        "sebelum 08:00 dan pindahkan unit ke area perkantoran sebelum 17:00. "
        "(2) Adakan promo akhir pekan di sekitar taman kota/area wisata pukul 11:00-15:00."
    )
