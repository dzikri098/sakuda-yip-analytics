from __future__ import annotations

import re
from pathlib import Path
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
FILES = {
    "users": ("data-pengguna-2026-11-20.csv", "Data pengguna"),
    "events": ("rekap-pelaksanaan-acara-2026-11-20.csv", "Rekap acara"),
    "aspirations": ("rekap-aspirasi-pemuda-2026-11-20.csv", "Aspirasi pemuda"),
}
REQUIRED_COLUMNS = {
    "users": ["Tanggal Registrasi", "Terakhir Diperbarui", "Provinsi", "Kabupaten / Kota", "Alamat Lengkap", "Status Verifikasi"],
    "events": ["Nama Program / Acara", "Kategori Program", "Status Pelaksanaan", "Total Pendaftar", "Kapasitas Kuota Pendaftaran"],
    "aspirations": ["Tanggal & Waktu", "Provinsi", "Kota / Kabupaten", "Kecamatan", "Kategori", "Topik Pelatihan", "Status"],
}
COLORS = ["#187E83", "#55A6A0", "#A9D2C8", "#E3B66D", "#E98768", "#8295B0"]

st.set_page_config(page_title="Analytics Pemuda Jawa Barat", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root{--ink:#19343A;--muted:#6E8388;--teal:#167E7A;--teal-dark:#0E615F;--line:#E2EBE9;--canvas:#F4F8F7;--white:#FFFFFF}
.stApp,[data-testid="stAppViewContainer"]{background:var(--canvas);color:var(--ink)}
[data-testid="stHeader"]{background:transparent}
[data-testid="stToolbar"]{right:1rem}
[data-testid="stSidebar"]{background:var(--white);border-right:1px solid var(--line)}
[data-testid="stSidebar"]>div:first-child{padding-top:1.1rem}
[data-testid="stSidebar"] *{color:var(--ink)}
.block-container{max-width:1540px;padding-top:2rem;padding-bottom:3rem}
[data-testid="stMetric"]{background:var(--white);border:1px solid var(--line);padding:18px 20px;border-radius:18px;box-shadow:0 5px 18px rgba(25,52,58,.035);min-height:118px}
[data-testid="stMetricLabel"]{color:var(--muted);font-size:13px;font-weight:600}
[data-testid="stMetricValue"]{color:var(--ink);font-size:28px;font-weight:700}
[data-testid="stMetricDelta"]{font-size:12px}
.eyebrow{color:var(--teal);font-size:11px;font-weight:800;letter-spacing:.14em;text-transform:uppercase}
.page-title{color:var(--ink);font-size:34px;font-weight:760;letter-spacing:-.04em;margin:.25rem 0 .3rem}
.page-subtitle{color:var(--muted);font-size:15px;margin:0 0 1.6rem;max-width:850px}
.warning-note{background:#FFF6E8;border:1px solid #F1D9AE;border-left:4px solid #D49A3E;padding:14px 17px;border-radius:12px;color:#6A4D20;font-size:13px;line-height:1.55;margin:1rem 0 1.4rem}
.info-card{background:var(--white);border:1px solid var(--line);border-radius:16px;padding:18px 20px;height:100%;box-shadow:0 5px 18px rgba(25,52,58,.035)}
.info-label{font-size:12px;color:var(--muted);font-weight:650;margin-bottom:8px}
.info-value{font-size:17px;color:var(--ink);font-weight:700;line-height:1.4}
.section-heading{font-size:19px;font-weight:730;color:var(--ink);letter-spacing:-.025em;margin:1.2rem 0 .65rem}
[data-testid="stSidebar"] [data-testid="stRadio"]>div{gap:7px;flex-direction:column}
[data-testid="stSidebar"] [data-testid="stRadio"] label{width:100%;box-sizing:border-box;background:#F2F6F5;border:1px solid transparent;border-radius:12px;padding:10px 12px;margin:0;transition:all .16s ease}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{background:#E9F2F0;border-color:#D9E7E4}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){background:var(--teal);border-color:var(--teal);color:white}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) *{color:white}
[data-testid="stButton"] button{border-radius:10px;border:1px solid var(--line);font-weight:650}
[data-testid="stButton"] button[kind="primary"]{background:var(--teal);border-color:var(--teal);color:white}
[data-testid="stButton"] button:hover{border-color:var(--teal);color:var(--teal-dark)}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:12px;overflow:hidden}
h2,h3{color:var(--ink);letter-spacing:-.025em}
hr{border-color:var(--line)}
</style>""", unsafe_allow_html=True)


def read_source(key, uploaded):
    filename, _ = FILES[key]
    try:
        if uploaded is not None:
            df = pd.read_csv(uploaded, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        else:
            path = ROOT / filename
            if not path.exists():
                return pd.DataFrame()
            df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        st.sidebar.error(f"{FILES[key][1]} tidak bisa dibaca. Periksa format CSV: {exc}")
        return pd.DataFrame()
    missing = [column for column in REQUIRED_COLUMNS[key] if column not in df.columns]
    if missing:
        st.sidebar.error(f"{FILES[key][1]} tidak cocok. Kolom wajib yang belum ada: {', '.join(missing)}")
        return pd.DataFrame()
    return df


def clean(value):
    value = "" if value is None else str(value).strip()
    return "" if value.lower() in {"nan", "none", "-", "—"} else re.sub(r"\s+", " ", value)


def dates(df, column):
    return pd.to_datetime(df[column].astype(str).str.strip(), errors="coerce", format="mixed") if column in df else pd.Series(pd.NaT, index=df.index)


def district_from_address(raw):
    """Extract only when the address explicitly labels a kecamatan."""
    text = clean(raw)
    match = re.search(r"\b(?:kecamatan|kec\.?)[\s:.-]*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ '\-]{1,45}?)(?=\s*(?:,|;|\.|\bkab(?:upaten)?\b|\bkota\b|\bprov(?:insi)?\b|\bkode\s*pos\b|$))", text, re.I) if text else None
    return re.sub(r"\s+", " ", match.group(1)).strip(" ,.;:-").title() if match else ""


def prepare_users(df):
    df = df.copy()
    if df.empty:
        return df
    df["_date"] = dates(df, "Tanggal Registrasi")
    df["_last_updated"] = dates(df, "Terakhir Diperbarui")
    df["_province"] = df["Provinsi"].map(clean)
    df["_city"] = df["Kabupaten / Kota"].map(clean)
    df["_district"] = df["Alamat Lengkap"].map(district_from_address)
    df["_verify"] = df["Status Verifikasi"].map(lambda x: clean(x) or "Tidak diketahui")
    return df


def prepare_aspirations(df):
    df = df.copy()
    if df.empty:
        return df
    df["_date"] = dates(df, "Tanggal & Waktu")
    df["_province"] = df["Provinsi"].map(clean)
    df["_city"] = df["Kota / Kabupaten"].map(clean)
    raw = df["Kecamatan"].map(clean)
    parsed = raw.map(district_from_address)
    # Short entries can be a district name; keep longer address-like text unassigned
    # unless it contains an explicit Kec/Kecamatan marker.
    short_candidate = raw.where(raw.str.len().le(35), "").map(lambda x: x.title() if x else "")
    df["_district"] = parsed.where(parsed.ne(""), short_candidate)
    return df


def nums(series):
    return pd.to_numeric(series.astype(str).str.replace(r"[^0-9,.-]", "", regex=True).str.replace(",", ".", regex=False), errors="coerce")


def options(values):
    return sorted({clean(x) for x in values if clean(x)})


def short_label(value, limit=38):
    value = clean(value)
    return value if len(value) <= limit else value[:limit - 1].rstrip() + "…"


def region_filter(df, city, district):
    out = df
    if not out.empty and city != "Semua kabupaten/kota" and "_city" in out:
        out = out[out["_city"] == city]
    if not out.empty and district != "Semua kecamatan" and "_district" in out:
        out = out[out["_district"] == district]
    return out


def date_filter(df, date_range):
    if df.empty or "_date" not in df or len(date_range) != 2:
        return df
    start = pd.Timestamp(date_range[0])
    end = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    return df[df["_date"].between(start, end, inclusive="both")]


def bounds(df):
    if df.empty or "_date" not in df or df["_date"].dropna().empty:
        return None, None
    return df["_date"].min().normalize(), df["_date"].max().normalize()


def header(kicker, title, subtitle):
    st.markdown(f'<div class="eyebrow">{kicker}</div><div class="page-title">{title}</div><div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def chart(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=8, r=8, t=16, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif", color="#52666C", size=12), colorway=COLORS, legend_title_text="")
    fig.update_xaxes(showgrid=False, linecolor="#E6ECEB")
    fig.update_yaxes(gridcolor="#E9EFEE", zeroline=False)
    return fig


def render_overview(users, events, aspirations, urange, arange, city, district):
    header("Analytics Pemuda Jawa Barat", "Ringkasan dampak dan jangkauan", "Pantau pertumbuhan akun, performa program, dan kebutuhan pemuda dalam satu ruang analitik.")
    u = region_filter(date_filter(users, urange), city, district)
    a = region_filter(date_filter(aspirations, arange), city, district)
    total_regs = int(nums(events["Total Pendaftar"]).fillna(0).sum()) if not events.empty and "Total Pendaftar" in events else 0
    k = st.columns(4)
    k[0].metric("Akun terdaftar", f"{len(u):,}".replace(",", "."))
    k[1].metric("Pendaftar program", f"{total_regs:,}".replace(",", "."), help="Jumlah dari rekap acara; bukan jumlah pengguna unik.")
    k[2].metric("Aspirasi masuk", f"{len(a):,}".replace(",", "."))
    k[3].metric("Acara dalam rekap", f"{len(events):,}")
    st.caption("Angka akun dan aspirasi mengikuti filter wilayah/periode. Pendaftar program adalah penjumlahan angka pada rekap acara, bukan orang unik.")
    st.markdown('<div class="warning-note">Filter wilayah dan periode diterapkan pada akun dan aspirasi. Rekap acara adalah agregat snapshot tanpa tanggal pendaftar atau wilayah peserta. Retensi dan konversi traffic → akun → pendaftaran perlu data sesi/kunjungan dan relasi pendaftar acara ke akun.</div>', unsafe_allow_html=True)
    left, right = st.columns([1.4, 1])
    with left:
        st.subheader("Pertumbuhan akun baru")
        st.caption("Jumlah akun yang dibuat pada tiap hari, minggu, atau bulan. Ini bukan jumlah kunjungan ke website.")
        gran = st.selectbox("Kelompok waktu", ["Harian", "Mingguan", "Bulanan"], index=2, key="overview_period")
        if not u.empty and u["_date"].notna().any():
            freq = {"Harian": "D", "Mingguan": "W-MON", "Bulanan": "MS"}[gran]
            trend = u.dropna(subset=["_date"]).set_index("_date").resample(freq).size().rename("Akun baru").reset_index()
            trend.columns = ["Periode", "Akun baru"]
            fig = px.area(trend, x="Periode", y="Akun baru", color_discrete_sequence=[COLORS[0]])
            fig.update_traces(line_width=2, fillcolor="rgba(24,126,131,.12)")
            st.plotly_chart(chart(fig), width="stretch")
        else:
            st.info("Belum ada data untuk filter ini.")
    with right:
        st.subheader("Aspirasi menurut kategori")
        st.caption("Jumlah aspirasi di setiap kategori setelah filter diterapkan.")
        if not a.empty and "Kategori" in a:
            cat = a["Kategori"].replace("", "Tidak dikategorikan").value_counts().rename_axis("Kategori").reset_index(name="Jumlah")
            cat = cat.sort_values("Jumlah", ascending=True)
            fig = px.bar(cat, x="Jumlah", y="Kategori", orientation="h", text="Jumlah", color_discrete_sequence=[COLORS[0]])
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_layout(showlegend=False, xaxis_title="Jumlah aspirasi", yaxis_title="")
            st.plotly_chart(chart(fig, 300), width="stretch")
        else:
            st.info("Belum ada data untuk filter ini.")
    st.subheader("Program dengan pendaftar terbanyak")
    st.caption("Acara diurutkan berdasarkan total pendaftar yang tercatat di rekap.")
    if not events.empty and "Total Pendaftar" in events:
        top = events.copy()
        top["_registrants"] = nums(top["Total Pendaftar"])
        top = top.dropna(subset=["_registrants"]).nlargest(8, "_registrants")
        if not top.empty:
            top["_label"] = top["Nama Program / Acara"].map(lambda x: short_label(x, 34))
            fig = px.bar(top.sort_values("_registrants"), x="_registrants", y="_label", orientation="h", hover_data={"Nama Program / Acara": True, "_registrants": ":,.0f", "_label": False}, color_discrete_sequence=[COLORS[0]])
            fig.update_layout(margin=dict(l=230, r=35, t=15, b=40), yaxis_title="", xaxis_title="Jumlah pendaftar")
            st.plotly_chart(chart(fig, 360), width="stretch")
        else:
            st.info("Angka pendaftar belum tersedia.")


def render_users(users, date_range, city, district):
    header("Pengguna", "Pertumbuhan dan profil akun", "Baca tren pendaftaran akun dan status verifikasi berdasarkan wilayah.")
    u = region_filter(date_filter(users, date_range), city, district)
    k = st.columns(3)
    k[0].metric("Akun pada filter", f"{len(u):,}".replace(",", "."))
    k[1].metric("Terverifikasi", f"{int(u['_verify'].str.lower().eq('verified').sum()):,}".replace(",", ".") if not u.empty else "0")
    k[2].metric("Belum terpetakan kecamatan", f"{int(u['_district'].eq('').sum()):,}".replace(",", ".") if not u.empty else "0")
    st.caption("‘Terverifikasi’ berarti status akun tercatat Verified. Kecamatan yang tidak terbaca dari alamat masuk hitungan belum terpetakan.")
    left, right = st.columns([1.4, 1])
    with left:
        st.subheader("Akun baru dari waktu ke waktu")
        st.caption("Setiap batang/titik menunjukkan berapa akun yang dibuat pada bulan tersebut.")
        if not u.empty and u["_date"].notna().any():
            trend = u.dropna(subset=["_date"]).set_index("_date").resample("MS").size().rename("Akun baru").reset_index()
            trend.columns = ["Bulan", "Akun baru"]
            st.plotly_chart(chart(px.line(trend, x="Bulan", y="Akun baru", markers=True, color_discrete_sequence=[COLORS[0]])), width="stretch")
        else:
            st.info("Belum ada data untuk filter ini.")
    with right:
        st.subheader("Status verifikasi")
        st.caption("Bandingkan jumlah akun yang sudah dan belum terverifikasi.")
        if not u.empty:
            stat = u["_verify"].value_counts().rename_axis("Status").reset_index(name="Jumlah")
            st.plotly_chart(chart(px.bar(stat, x="Status", y="Jumlah", color="Status", color_discrete_sequence=COLORS)), width="stretch")
        else:
            st.info("Belum ada data untuk filter ini.")
    st.subheader("Sebaran kabupaten/kota")
    st.caption("Wilayah diurutkan dari jumlah akun terbanyak. ‘Belum diisi’ berarti kolom wilayah kosong.")
    if not u.empty:
        area = u["_city"].replace("", "Belum diisi").value_counts().head(15).rename_axis("Kabupaten/kota").reset_index(name="Akun")
        st.plotly_chart(chart(px.bar(area.sort_values("Akun"), x="Akun", y="Kabupaten/kota", orientation="h", color_discrete_sequence=[COLORS[1]]), 430), width="stretch")
    st.caption("Kecamatan diekstrak hanya bila alamat menyebut ‘Kec.’ atau ‘Kecamatan’ secara eksplisit. Data pribadi tidak ditampilkan.")


def render_events(events, city, district):
    header("Program acara", "Kinerja pendaftaran program", "Bandingkan minat pendaftar, kapasitas, dan status pelaksanaan acara.")
    if city != "Semua kabupaten/kota" or district != "Semua kecamatan":
        st.info("Rekap acara tidak memiliki wilayah peserta; filter wilayah tidak diterapkan di halaman ini.")
    if events.empty:
        st.info("Rekap acara belum tersedia.")
        return
    e = events.copy()
    e["_registrants"] = nums(e["Total Pendaftar"])
    e["_capacity"] = nums(e["Kapasitas Kuota Pendaftaran"])
    e["_fill"] = (e["_registrants"] / e["_capacity"] * 100).where(e["_capacity"] > 0)
    k = st.columns(3)
    k[0].metric("Total pendaftar di rekap", f"{int(e['_registrants'].fillna(0).sum()):,}".replace(",", "."))
    k[1].metric("Acara dengan data pendaftar", f"{int(e['_registrants'].notna().sum()):,}")
    k[2].metric("Acara dengan kuota", f"{int(e['_capacity'].gt(0).sum()):,}")
    st.caption("Total ini menjumlahkan angka per acara. Satu orang yang mendaftar ke beberapa acara dapat terhitung beberapa kali.")
    f1, f2 = st.columns(2)
    with f1:
        category = st.selectbox("Kategori program", ["Semua kategori"] + options(e.get("Kategori Program", [])), key="event_cat")
    with f2:
        status = st.selectbox("Status pelaksanaan", ["Semua status"] + options(e.get("Status Pelaksanaan", [])), key="event_status")
    st.caption("Pilih kategori atau status untuk mempersempit daftar dan grafik acara.")
    if category != "Semua kategori":
        e = e[e["Kategori Program"] == category]
    if status != "Semua status":
        e = e[e["Status Pelaksanaan"] == status]
    e["_label"] = e["Nama Program / Acara"].map(lambda name: short_label(name, 42))
    st.subheader("Pendaftar per program")
    st.caption("Program dengan pendaftar terbanyak ditampilkan lebih atas. Arahkan kursor ke batang untuk melihat nama lengkap dan jumlahnya.")
    ranked = e.dropna(subset=["_registrants"]).nlargest(12, "_registrants")
    if not ranked.empty:
        fig = px.bar(
            ranked.sort_values("_registrants"), x="_registrants", y="_label", orientation="h",
            hover_data={"Nama Program / Acara": True, "_registrants": ":,.0f", "_label": False},
            color_discrete_sequence=[COLORS[0]],
        )
        fig.update_layout(margin=dict(l=270, r=45, t=15, b=45), yaxis_title="", xaxis_title="Jumlah pendaftar")
        st.plotly_chart(chart(fig, max(390, 36 * len(ranked) + 90)), width="stretch")
    else:
        st.info("Angka pendaftar belum tersedia.")

    st.subheader("Keterisian kuota")
    st.caption("Persentase dihitung dari jumlah pendaftar dibagi kuota. Grafik hanya memuat acara yang memiliki data kuota.")
    fill = e.dropna(subset=["_fill"]).nlargest(10, "_fill")
    if not fill.empty:
        fig = px.bar(
            fill.sort_values("_fill"), x="_fill", y="_label", orientation="h",
            hover_data={"Nama Program / Acara": True, "_fill": ":.1f", "_label": False},
            color_discrete_sequence=[COLORS[3]],
        )
        fig.update_layout(margin=dict(l=270, r=45, t=15, b=45), yaxis_title="", xaxis_title="Keterisian kuota (%)")
        fig.update_xaxes(ticksuffix="%")
        st.plotly_chart(chart(fig, max(350, 36 * len(fill) + 90)), width="stretch")
    else:
        st.info("Kuota belum tersedia pada acara yang dipilih.")
    cols = [c for c in ["ID Acara", "Nama Program / Acara", "Kategori Program", "Status Pelaksanaan", "Tanggal Buka Pendaftaran", "Total Pendaftar", "Kapasitas Kuota Pendaftaran", "Persentase Kehadiran (%)"] if c in e]
    st.subheader("Daftar acara")
    st.caption("Tabel ini memuat nama lengkap dan ringkasan setiap acara sesuai filter kategori/status.")
    st.dataframe(e[cols], width="stretch", hide_index=True)
    st.caption("Angka pendaftar berasal dari rekap acara, bukan jumlah pengguna unik. Data ini tidak memuat wilayah peserta.")


def render_sakuda(users, city, district):
    launch = date(2026, 10, 9)
    fixed_cutoff = date(2026, 11, 20)
    header("Program SAKUDA", "Retensi pengguna baru", "Ikuti cohort akun yang mendaftar sejak peluncuran SAKUDA pada 9 Oktober 2026.")
    if users.empty:
        st.info("Data pengguna belum tersedia.")
        return
    latest = users["_date"].dropna().max()
    if pd.isna(latest) or latest.date() < launch:
        st.info("Belum ada pendaftaran akun pada atau setelah tanggal peluncuran SAKUDA.")
        return
    max_day = min(latest.date(), fixed_cutoff)
    period = st.date_input("Periode cohort", value=(launch, max_day), min_value=launch, max_value=max_day, key="sakuda_period")
    st.caption("Pilih rentang tanggal daftar akun. Tanggal awal bawaan adalah tanggal peluncuran SAKUDA.")
    if len(period) != 2:
        st.info("Pilih tanggal awal dan akhir untuk melihat cohort.")
        return
    start, end = period
    cohort = users[(users["_date"].dt.date >= start) & (users["_date"].dt.date <= end)].copy()
    cohort = region_filter(cohort, city, district)
    if cohort.empty:
        st.info("Belum ada akun baru pada periode atau wilayah yang dipilih.")
        return

    cohort["_updated_after_signup"] = cohort["_last_updated"] > cohort["_date"]
    new_users = len(cohort)
    updated_after = int(cohort["_updated_after_signup"].sum())
    proxy_rate = updated_after / new_users * 100 if new_users else 0
    mapped_cities = cohort["_city"].replace("", pd.NA).nunique()
    metrics = st.columns(3)
    metrics[0].metric("Akun baru sejak peluncuran", f"{new_users:,}".replace(",", "."))
    metrics[1].metric("Diperbarui setelah mendaftar · proxy", f"{updated_after:,}".replace(",", "."), f"{proxy_rate:.1f}% dari cohort")
    metrics[2].metric("Kabupaten/kota terwakili", f"{mapped_cities:,}".replace(",", "."))
    st.caption("Cohort adalah akun yang tanggal daftarnya berada pada rentang terpilih. Ubah wilayah di sidebar untuk membatasi hasil.")
    st.markdown('<div class="warning-note">Angka ini adalah cohort akun yang dibuat pada periode terpilih, belum tentu pendaftar yang berasal dari SAKUDA karena sumber akuisisi tidak ada di CSV. Kolom “Terakhir Diperbarui” dipakai hanya sebagai proxy aktivitas lanjutan; ini bukan retensi login/penggunaan. Untuk retensi sebenarnya, perlu log login/sesi atau aktivitas per user.</div>', unsafe_allow_html=True)

    cohort["Minggu daftar"] = cohort["_date"].dt.to_period("W-SUN").dt.start_time
    weekly = cohort.groupby("Minggu daftar", as_index=False).agg(
        **{"Akun baru": ("_date", "size"), "Diperbarui setelah daftar": ("_updated_after_signup", "sum")}
    )
    weekly["Proxy aktivitas lanjutan (%)"] = weekly["Diperbarui setelah daftar"] / weekly["Akun baru"] * 100
    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Pendaftaran akun per minggu")
        st.caption("Batang hijau menunjukkan akun baru. Batang kuning menunjukkan akun yang datanya diperbarui setelah pendaftaran.")
        plot = weekly.melt(id_vars="Minggu daftar", value_vars=["Akun baru", "Diperbarui setelah daftar"], var_name="Ukuran", value_name="Pengguna")
        fig = px.bar(plot, x="Minggu daftar", y="Pengguna", color="Ukuran", barmode="group", color_discrete_sequence=[COLORS[0], COLORS[3]])
        st.plotly_chart(chart(fig, 370), width="stretch")
    with right:
        st.subheader("Proxy aktivitas lanjutan per cohort")
        st.caption("Persentase akun per minggu yang kolom ‘Terakhir Diperbarui’-nya lebih baru dari waktu daftar; bukan bukti login kembali.")
        fig = px.line(weekly, x="Minggu daftar", y="Proxy aktivitas lanjutan (%)", markers=True, color_discrete_sequence=[COLORS[0]])
        fig.update_yaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(chart(fig, 370), width="stretch")
    st.subheader("Sebaran cohort menurut kabupaten/kota")
    st.caption("Jumlah akun baru per wilayah. Data tanpa kabupaten/kota ditampilkan sebagai ‘Belum diisi’.")
    areas = cohort["_city"].replace("", "Belum diisi").value_counts().head(12).rename_axis("Kabupaten/kota").reset_index(name="Akun baru")
    area_col, table_col = st.columns([1.2, 1])
    with area_col:
        fig = px.bar(areas.sort_values("Akun baru"), x="Akun baru", y="Kabupaten/kota", orientation="h", color_discrete_sequence=[COLORS[1]])
        st.plotly_chart(chart(fig, 400), width="stretch")
    with table_col:
        st.dataframe(weekly.rename(columns={"Minggu daftar": "Cohort mingguan"}), width="stretch", hide_index=True)


def render_aspirations(aspirations, date_range, city, district):
    header("Suara Pemuda", "Aspirasi dan kebutuhan pemuda", "Lihat tema umum, lalu persempit berdasarkan wilayah, topik, dan status.")
    a = region_filter(date_filter(aspirations, date_range), city, district)
    if a.empty:
        st.info("Tidak ada aspirasi pada filter ini.")
        return
    k = st.columns(3)
    k[0].metric("Aspirasi", f"{len(a):,}".replace(",", "."))
    k[1].metric("Kabupaten/kota terwakili", f"{a['_city'].replace('', pd.NA).nunique():,}".replace(",", "."))
    k[2].metric("Kecamatan terpetakan", f"{a['_district'].replace('', pd.NA).nunique():,}".replace(",", "."))
    st.caption("Semua angka mengikuti filter wilayah dan periode di sidebar. Kecamatan hanya dihitung jika nilainya berhasil dikenali.")
    left, right = st.columns(2)
    with left:
        st.subheader("Aspirasi menurut kategori")
        st.caption("Kategori membantu merangkum jenis kebutuhan atau masukan yang dikirim pemuda.")
        cat = a["Kategori"].replace("", "Tidak dikategorikan").value_counts().rename_axis("Kategori").reset_index(name="Jumlah")
        st.plotly_chart(chart(px.bar(cat.sort_values("Jumlah"), x="Jumlah", y="Kategori", orientation="h", color_discrete_sequence=[COLORS[0]])), width="stretch")
    with right:
        st.subheader("Topik pelatihan")
        st.caption("Topik yang paling sering diminta ditampilkan di bagian atas.")
        topics = a["Topik Pelatihan"].replace("", "Tidak diisi").value_counts().head(12).rename_axis("Topik").reset_index(name="Jumlah")
        topics["_label"] = topics["Topik"].map(lambda x: short_label(x, 32))
        fig = px.bar(topics.sort_values("Jumlah"), x="Jumlah", y="_label", orientation="h", hover_data={"Topik": True, "Jumlah": True, "_label": False}, color_discrete_sequence=[COLORS[1]])
        fig.update_layout(margin=dict(l=185, r=25, t=15, b=35), yaxis_title="", xaxis_title="Jumlah aspirasi")
        st.plotly_chart(chart(fig, 390), width="stretch")
    l2, r2 = st.columns([1, 1.2])
    with l2:
        st.subheader("Status tindak lanjut")
        st.caption("Menunjukkan tahap penanganan yang tercatat oleh admin.")
        status = a["Status"].replace("", "Belum diisi").value_counts().rename_axis("Status").reset_index(name="Jumlah")
        st.plotly_chart(chart(px.pie(status, names="Status", values="Jumlah", hole=.62, color_discrete_sequence=COLORS), 320), width="stretch")
    with r2:
        st.subheader("Aspirasi per kabupaten/kota")
        st.caption("Bandingkan jumlah masukan dari tiap wilayah yang terisi.")
        regions = a["_city"].replace("", "Belum diisi").value_counts().head(12).rename_axis("Kabupaten/kota").reset_index(name="Aspirasi")
        st.plotly_chart(chart(px.bar(regions.sort_values("Aspirasi"), x="Aspirasi", y="Kabupaten/kota", orientation="h", color_discrete_sequence=[COLORS[3]]), 320), width="stretch")
    st.subheader("Eksplorasi aspirasi")
    st.caption("Cari berdasarkan judul, topik, atau kategori. Pilih satu baris untuk melihat atribut ringkas aspirasi.")
    query = st.text_input("Cari judul atau topik", placeholder="Contoh: kewirausahaan, public speaking")
    selected = a.copy()
    if query:
        mask = pd.Series(False, index=selected.index)
        for col in ["Judul Aspirasi", "Topik Pelatihan", "Kategori"]:
            mask |= selected[col].astype(str).str.contains(query, case=False, na=False)
        selected = selected[mask]
    view = [c for c in ["Tanggal & Waktu", "Kota / Kabupaten", "Kecamatan", "Kategori", "Topik Pelatihan", "Format Pelatihan", "Judul Aspirasi", "Status"] if c in selected]
    st.dataframe(selected[view].sort_values("Tanggal & Waktu", ascending=False), width="stretch", hide_index=True)
    st.caption("Nama, email, deskripsi lengkap, dan catatan admin tidak ditampilkan pada tabel ringkasan untuk menjaga privasi.")


pages = ["Ringkasan", "Pengguna", "Program acara", "SAKUDA", "Suara Pemuda"]
if "page" not in st.session_state:
    st.session_state.page = "Ringkasan"
with st.sidebar:
    st.markdown("## Analytics YIP")
    st.caption("Dashboard analitik pemuda")
    st.markdown("### Navigasi")
    st.session_state.page = st.radio("Navigasi", pages, index=pages.index(st.session_state.page), label_visibility="collapsed", key="page_nav")
    st.divider()
    filters_slot = st.empty()
    uploads_slot = st.empty()

uploads = {}
with uploads_slot.container():
    with st.expander("Perbarui sumber data", expanded=False):
        st.caption("Unggah ekspor terbaru. File hanya menggantikan data bawaan selama sesi ini.")
        for key, (filename, label) in FILES.items():
            uploads[key] = st.file_uploader(f"{label} · {filename}", type=["csv"], key=f"upload_{key}", help="Unggah ekspor terbaru untuk menggantikan file bawaan selama sesi ini.")

users = prepare_users(read_source("users", uploads["users"]))
events = read_source("events", uploads["events"])
aspirations = prepare_aspirations(read_source("aspirations", uploads["aspirations"]))

all_cities = options(list(users.get("_city", [])) + list(aspirations.get("_city", [])))
u_min, u_max = bounds(users)
a_min, a_max = bounds(aspirations)
valid = [x for x in [u_min, u_max, a_min, a_max] if x is not None]
with filters_slot.container():
    st.markdown("### Filter wilayah")
    city = st.selectbox("Kabupaten/kota", ["Semua kabupaten/kota"] + all_cities, key="filter_city")
    st.caption("Pilih wilayah untuk menyaring data akun dan aspirasi.")
    districts = []
    if city == "Semua kabupaten/kota":
        districts = options(list(users.get("_district", [])) + list(aspirations.get("_district", [])))
    else:
        if not users.empty:
            districts += options(users.loc[users["_city"].eq(city), "_district"])
        if not aspirations.empty:
            districts += [d for d in options(aspirations.loc[aspirations["_city"].eq(city), "_district"]) if d not in districts]
    district = st.selectbox("Kecamatan", ["Semua kecamatan"] + districts, key="filter_district")
    st.caption("Daftar kecamatan menyesuaikan kabupaten/kota; alamat yang tidak jelas tidak ditebak.")
    st.markdown("### Periode")
    st.caption("Pilih tanggal awal dan akhir untuk menyaring akun serta aspirasi. Halaman SAKUDA memiliki rentang cohort khusus.")
    if valid:
        min_date = min(x for x in [u_min, a_min] if x is not None)
        max_date = max(x for x in [u_max, a_max] if x is not None)
        date_range = st.date_input("Rentang tanggal", value=(min_date.date(), max_date.date()), min_value=min_date.date(), max_value=max_date.date(), key="filter_dates")
    else:
        date_range = ()
    st.divider()
    st.caption("Ekspor saat ini adalah snapshot, bukan koneksi langsung ke database produksi.")

if st.session_state.page == "Ringkasan":
    render_overview(users, events, aspirations, date_range, date_range, city, district)
elif st.session_state.page == "Pengguna":
    render_users(users, date_range, city, district)
elif st.session_state.page == "Program acara":
    render_events(events, city, district)
elif st.session_state.page == "SAKUDA":
    render_sakuda(users, city, district)
else:
    render_aspirations(aspirations, date_range, city, district)

st.markdown("---")
st.caption("Analytics YIP · Data bersumber dari ekspor CSV.")
