# Opsi Visualisasi Dashboard YIP

**Basis data:** ekspor 20 November 2026  
**Tujuan:** membaca perjalanan pendaftaran akun ke program, memahami jangkauan wilayah, dan merangkum aspirasi pemuda.

## Ringkasan data yang tersedia

| Sumber | Cakupan | Catatan |
|---|---:|---|
| Pengguna | 30.048 akun | Memiliki waktu registrasi, status verifikasi, provinsi, kabupaten/kota, dan alamat bebas. Tidak ada data sesi atau sumber traffic. |
| Pelaksanaan acara | 40 acara | 34 acara berisi angka pendaftar nonzero; satu acara tidak memiliki angka pendaftar. Rekap ini tidak menyertakan ID pengguna pendaftar. |
| Aspirasi pemuda | 196 aspirasi | 193 masuk pada November 2026; tersedia kategori, topik, format, status, kabupaten/kota, dan kolom kecamatan yang tidak konsisten. |

**Batas interpretasi:** data saat ini dapat menunjukkan pertumbuhan akun dan jumlah pendaftar per acara. Data ini belum dapat menghitung conversion rate traffic → akun → pendaftaran program, cohort retention, atau pendaftar acara per wilayah. Untuk itu dibutuhkan log kunjungan/sesi dengan sumber kampanye serta relasi aman `user_id ↔ event_id` dan timestamp pendaftaran acara.

## Opsi 1 — Dashboard pimpinan: ringkasan dan eksplorasi

**Direkomendasikan** untuk halaman utama analitik karena memberi gambaran umum tanpa mencampur angka dari sumber yang belum terhubung.

### Susunan halaman

1. **Ringkasan** — KPI akun terdaftar, akun baru per periode, acara aktif, total pendaftar acara (hasil penjumlahan rekap), dan aspirasi masuk. Setiap KPI menunjukkan periode dan sumber.
2. **Pertumbuhan akun** — grafik harian/mingguan/bulanan dari `Tanggal Registrasi`; bandingkan akun baru dengan kumulatif akun. Tambahkan status verifikasi sebagai breakdown.
3. **Program & pendaftaran** — ranking pendaftar per acara, tren jumlah pendaftar menurut tanggal buka pendaftaran, status acara, kuota dan keterisian jika tersedia. Beri label jelas bahwa ini rekap acara, bukan konversi dari traffic.
4. **Suara Pemuda** — tren aspirasi masuk, kategori, topik yang paling banyak diminta, format pelatihan, dan status tindak lanjut. Tampilkan daftar judul/deskripsi setelah filter untuk eksplorasi kualitatif.
5. **Jangkauan wilayah** — ranking kabupaten/kota dan kecamatan yang terpetakan, dengan tabel yang lebih mudah dibaca daripada peta bila geocoding belum tersedia.

### Filter

- Filter umum yang tersedia lintas sumber: **rentang tanggal**, **provinsi**, **kabupaten/kota**.
- Filter aspirasi: **kecamatan**, kategori, topik pelatihan, format, dan status.
- Filter acara: kategori program, format, status pelaksanaan/pembukaan pendaftaran, periode acara, dan nama program.
- Filter pengguna: status verifikasi, jenis kelamin, tipe akun, dan periode registrasi.
- Tampilkan filter per bagian/sumber data. Jangan membuat satu filter global seolah-olah seluruh sumber memiliki relasi pengguna-acara yang sama.

### Tombol khusus SAKUDA

Pasang tombol permanen **“SAKUDA”** di dekat filter program atau sebagai kartu pintasan yang menonjol. Tombol membuka halaman detail khusus untuk acara **“Opening dan Pelaksanaan SAKUDA” (ID acara 105)**, memuat profil acara, periode, status, grafik pendaftar harian bila data pendaftaran tersedia, tren wilayah, dan ringkasan peserta.

Pada ekspor saat ini, baris SAKUDA belum memuat total pendaftar, kuota, peserta terkonfirmasi, maupun presensi. Karena itu, halaman detail harus menampilkan **“Data belum tersedia”**, bukan angka nol. Setelah data peserta SAKUDA disediakan, tombol dapat mengarah ke metrik pendaftar, verifikasi, kehadiran, dan asal wilayah.

## Opsi 2 — Tiga ruang analitik terpisah

Gunakan tab utama **Pengguna**, **Program Acara**, dan **Suara Pemuda**. Tiap tab memiliki KPI, grafik, dan filter sesuai skema sumbernya. Tombol SAKUDA menjadi tab/pintasan khusus di ruang Program Acara. Opsi ini cocok jika tim operasional tiap bidang perlu fokus pada tindak lanjut masing-masing.

Kelebihan: filter tidak membingungkan dan setiap angka punya konteks. Kekurangan: hubungan lintas perjalanan pengguna harus dibaca manual hingga data relasi tersedia.

## Opsi 3 — Funnel retensi setelah pelacakan ditambahkan

Jika tujuan utama adalah mengukur retensi traffic sampai daftar program, tambahkan pencatatan tahapan berikut:

`kunjungan landing/acara → klik daftar → mulai formulir → akun dibuat → pendaftaran acara terkirim → pendaftaran terkonfirmasi → hadir`

Simpan `anonymous_session_id` sebelum login, lalu tautkan ke `user_id` setelah autentikasi, serta catat `event_id`, timestamp, dan UTM/source secara konsisten. Dashboard dapat menampilkan conversion rate antar tahap, abandonment, cohort minggu/bulan, retensi D7/D30, dan perbandingan kanal. Gunakan ID pseudonim untuk analitik; jangan masukkan NIK, email, nomor telepon, atau alamat mentah ke grafik.

## Penanganan filter kecamatan dari alamat

Kolom alamat akun berisi 12.612 nilai nonkosong dari 30.048 akun dan merupakan teks bebas. Sekitar 7.329 alamat memiliki penanda eksplisit seperti `Kec.`/`Kecamatan`; sisanya bisa berupa nama kota, jalan, desa, atau teks yang tidak cukup untuk memastikan kecamatan. Kolom kecamatan aspirasi juga banyak berisi alamat panjang atau nama yang tidak baku.

Rekomendasi implementasi:

1. Buat kolom turunan **Kecamatan (hasil normalisasi)** dari penanda eksplisit `Kec.`/`Kecamatan`, lalu cocokkan dengan daftar kecamatan resmi berdasarkan kabupaten/kota.
2. Bila kecamatan tidak dapat dipastikan, isi **Belum terpetakan**; jangan menebak dari nama jalan/desa tanpa lookup yang tervalidasi.
3. Simpan nilai sumber dan nilai normalisasi terpisah, sertakan indikator keyakinan, serta sediakan koreksi admin untuk pencocokan yang meragukan.
4. Filter kecamatan bergantung pada kabupaten/kota yang dipilih; pilihan hanya memuat kecamatan yang lolos normalisasi.
5. Terapkan metode yang sama pada aspirasi. Untuk pemetaan wilayah yang andal, prioritaskan penambahan field kecamatan terstruktur pada formulir.

## Visual yang disarankan

| Pertanyaan | Visual |
|---|---|
| Apakah pertumbuhan akun naik/turun? | Grafik garis jumlah akun baru per hari/minggu dan garis kumulatif |
| Program mana paling banyak menarik pendaftar? | Bar chart horizontal dengan label jumlah dan status acara |
| Apakah kuota program terserap? | Progress bar keterisian kuota; sembunyikan jika kuota tidak tersedia |
| Dari mana aspirasi berasal? | Bar chart kabupaten/kota, lalu drill-down kecamatan terpetakan |
| Apa kebutuhan pemuda yang paling sering muncul? | Bar chart kategori/topik dan tabel aspirasi terfilter |
| Aspirasi sudah ditangani? | Bar/status funnel berdasarkan status, dilengkapi umur aspirasi bila proses tindak lanjut tersedia |

## Catatan kualitas dan privasi

- 29.956 dari 30.048 akun berstatus `Pending` pada ekspor ini; tampilkan status dan tanggal snapshot agar angka tidak dianggap kondisi langsung.
- Nilai pekerjaan, alamat, dan wilayah perlu normalisasi sebelum dibandingkan.
- Jangan menyamakan jumlah akun dengan jumlah pengunjung unik.
- Aspirasi memuat informasi pribadi dan narasi bebas. Batasi akses ke detail, hilangkan identitas dari agregasi, dan jangan menampilkan kutipan yang dapat mengidentifikasi pengirim tanpa kebutuhan dan izin yang sesuai.
- Angka SAKUDA yang kosong harus tetap kosong/tidak tersedia, bukan diisi nol.
