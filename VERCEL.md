# MEC Mart - Vercel

Project ini menggunakan Flask + MySQL.

## Lokal

1. Import `database.sql` ke MySQL/phpMyAdmin.
2. `pip install -r requirements.txt`
3. `python app.py`
4. Buka `http://127.0.0.1:5000`

## Vercel

Vercel dapat mendeteksi Flask secara langsung. Project tetap memakai `app.py` sebagai entrypoint.

### Environment Variables

Tambahkan di Vercel > Project > Settings > Environment Variables:

- `DB_HOST`
- `DB_PORT` (biasanya `3306`)
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `DB_TIMEOUT` (opsional, default 10)
- `SECRET_KEY`

Jangan gunakan `127.0.0.1` untuk `DB_HOST` di Vercel. Gunakan host MySQL online.

## Database online

Export/import `database.sql` ke provider MySQL online yang mengizinkan koneksi dari Vercel. XAMPP MySQL di laptop tidak bisa menjadi database production untuk deployment Vercel.

## Deploy via GitHub

1. Buat repository GitHub.
2. Upload semua isi folder project ini.
3. Vercel > Add New Project > Import Git Repository.
4. Pilih repository MEC Mart.
5. Tambahkan environment variables database.
6. Deploy.

## Penting

`database.sql` adalah schema + seed awal. Jangan mengimpor ulang ke database production jika sudah ada pesanan karena script tersebut melakukan DROP TABLE.
