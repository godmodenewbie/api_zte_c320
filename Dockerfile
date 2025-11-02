# 1. Gunakan base image Python yang ramping
FROM python:3.10-slim

# 2. Set direktori kerja di dalam container
WORKDIR /app

# 3. Salin file requirements.txt terlebih dahulu untuk caching
COPY requirements.txt requirements.txt

# 4. Install semua dependensi
# --no-cache-dir digunakan agar image lebih kecil
RUN pip install --no-cache-dir -r requirements.txt

# Perintah ini untuk debugging: mencetak semua paket yang terinstall
RUN pip freeze

# 5. Salin semua file kode aplikasi
COPY . .

# 6. Expose port yang akan digunakan oleh uvicorn
EXPOSE 8000

# 7. Definisikan command untuk menjalankan aplikasi saat container启动
# Gunakan --host 0.0.0.0 agar aplikasi bisa diakses dari luar container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
