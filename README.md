# Analytics YIP — Streamlit

Dashboard analitik interaktif berbasis Python dan Streamlit untuk membaca ekspor pengguna, rekap program/acara, dan aspirasi pemuda.

## Menjalankan secara lokal

Gunakan Python 3.10 atau yang lebih baru.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

Di Windows, aktifkan virtual environment dengan `.venv\\Scripts\\activate`.

Secara default aplikasi membaca tiga file CSV di folder proyek. Untuk memperbarui tampilan tanpa mengubah kode, unggah ekspor CSV terbaru melalui sidebar; unggahan menggantikan data bawaan selama sesi Streamlit berjalan.

## Deploy ke Streamlit Community Cloud

1. Simpan `app.py`, `requirements.txt`, dan file pendukung aplikasi di repository GitHub.
2. Buka Streamlit Community Cloud, pilih **Create app**, lalu tentukan repository, branch, dan `app.py` sebagai entry point.
3. Deploy dan gunakan URL aplikasi yang disediakan.
4. Untuk pembaruan, push perubahan ke branch yang dipilih.

## Data dan privasi

Ekspor pengguna memuat data pribadi. Jangan commit CSV mentah ke repository publik dan jangan menjadikan aplikasi publik dengan data pribadi tertanam di dalam source. Gunakan repository privat serta pembatasan akses aplikasi, atau sambungkan aplikasi ke sumber data privat yang memiliki kontrol akses. File yang diunggah melalui aplikasi hanya dipakai selama sesi berjalan; untuk pembaruan otomatis/terjadwal, hubungkan ke database atau storage privat dengan kredensial melalui Streamlit Secrets.

File CSV yang dipakai secara lokal diabaikan Git melalui `.gitignore`. Jika file tersebut sebelumnya sudah pernah di-commit, keluarkan dari index Git sebelum push.

## Batas data saat ini

- Grafik pertumbuhan akun memakai timestamp registrasi, bukan kunjungan atau traffic situs.
- Retensi dan conversion funnel memerlukan log sesi/kunjungan serta relasi akun dengan pendaftaran acara.
- Filter kecamatan diambil dari teks alamat hanya jika nama kecamatan ditandai dengan jelas. Aspirasi dengan nilai kecamatan pendek diperlakukan sebagai kandidat kecamatan; tetap perlu validasi terhadap daftar wilayah resmi.
- Rekap acara tidak menyediakan wilayah peserta. Baris SAKUDA saat ini belum menyediakan total pendaftar, kuota, konfirmasi, atau presensi, sehingga aplikasi menampilkan “Data belum tersedia”.
- Tampilan aspirasi hanya memuat judul dan atribut terpilih; identitas dan deskripsi lengkap tidak ditampilkan pada tabel analitik.
