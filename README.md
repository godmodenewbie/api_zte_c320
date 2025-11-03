# API Status ONT ZTE C320

Sebuah servis API sederhana yang dibangun menggunakan Python, FastAPI, dan Pysnmp untuk memonitor status Optical Network Terminal (ONT) pada perangkat OLT ZTE C320 melalui protokol SNMP.

Aplikasi ini menggunakan pustaka `pysnmp` dengan mode asynchronous untuk memastikan performa yang tinggi saat melakukan polling ke perangkat jaringan.

## Fitur

- **Framework Modern:** Dibangun di atas FastAPI yang cepat dan modern.
- **Asynchronous SNMP:** Menggunakan `pysnmp.hlapi.asyncio` untuk operasi non-blocking, memungkinkan polling ke banyak perangkat secara efisien.
- **Parsing Status:** Menerjemahkan kode status integer dari SNMP menjadi teks yang mudah dibaca (`working`, `LOS`, `DyingGasp`).
- **Dokumentasi Otomatis:** Dilengkapi dengan dokumentasi interaktif dari FastAPI (Swagger UI & ReDoc).

---

## Konfigurasi

Aplikasi ini dikonfigurasi melalui environment variables.

- `SNMP_COMMUNITY_STRING`: Mengatur SNMP community string yang akan digunakan untuk query ke OLT.
  - **Default:** `public`

Untuk mengubahnya saat menggunakan Docker, cukup edit file `docker-compose.yml`:

```yaml
environment:
  - SNMP_COMMUNITY_STRING=komunitas_rahasia_anda
```

---

## Cara Menjalankan

Bagian ini menjelaskan cara menjalankan aplikasi secara manual menggunakan environment Python.

Pastikan Anda memiliki Python 3.8+ terinstall.

1.  **Clone Repositori (Opsional)**
    ```bash
    # Jika Anda menggunakan git
    git clone <url-repositori-anda>
    cd api_zte_c320
    ```

2.  **Buat dan Aktifkan Virtual Environment (Direkomendasikan)**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    # Untuk Windows: venv\Scripts\activate
    ```

3.  **Install Dependensi**
    Dari dalam direktori proyek, jalankan perintah berikut untuk menginstall semua pustaka yang dibutuhkan:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Jalankan Server API**
    Gunakan `uvicorn` untuk menjalankan server aplikasi:
    ```bash
    uvicorn main:app --reload
    ```
    - `--reload`: Flag ini akan membuat server otomatis restart setiap kali ada perubahan pada kode. Cocok untuk development.

Server akan berjalan di `http://127.0.0.1:8000`.

---

## Menjalankan dengan Docker Compose

Cara yang direkomendasikan untuk menjalankan aplikasi ini adalah menggunakan Docker dan Docker Compose. Ini menyederhanakan proses setup dan deployment.

Pastikan Docker dan Docker Compose sudah terinstall di sistem Anda.

1.  **Build dan Jalankan Service**
    Dari direktori utama proyek (yang berisi `docker-compose.yml`), jalankan perintah berikut:
    ```bash
    docker-compose up --build -d
    ```
    - `up`: Membuat dan menjalankan container.
    - `--build`: Memaksa Docker untuk membangun ulang image dari `Dockerfile` jika ada perubahan.
    - `-d`: Menjalankan container di background (detached mode).

2.  **Verifikasi**
    Aplikasi sekarang berjalan di dalam container dan bisa diakses dari komputer Anda di `http://127.0.0.1:8000`.
    ```bash
    curl -X GET "http://127.0.0.1:8000/olt/192.168.100.1/onts/status"
    ```

3.  **Melihat Logs (Opsional)**
    Untuk melihat output atau log dari aplikasi yang berjalan di container:
    ```bash
    docker-compose logs -f
    ```

4.  **Menghentikan Service**
    Untuk menghentikan dan menghapus container yang dibuat oleh Docker Compose:
    ```bash
    docker-compose down
    ```

---

## Dokumentasi API

Aplikasi ini menyediakan satu endpoint utama untuk mengambil status ONT.

### Get ONT Status

Mengambil daftar semua ONT beserta statusnya dari OLT tertentu.

- **Method:** `GET`
- **URL:** `/olt/{olt_ip}/onts/status`

#### Parameters

- **Path Parameter:**
  - `olt_ip` (string, **required**): Alamat IP dari perangkat OLT ZTE yang akan di-query.
- **Query Parameter:**
  - `community` (string, *optional*): Community string SNMP yang ingin digunakan untuk request ini. Jika tidak diisi, akan menggunakan nilai default yang diatur di server.

#### Contoh Penggunaan (cURL)

- **Tanpa community string (menggunakan default server):**
  ```bash
  curl -X GET "http://127.0.0.1:8000/olt/192.168.100.1/onts/status"
  ```

- **Dengan community string spesifik:**
  ```bash
  curl -X GET "http://127.0.0.1:8000/olt/192.168.100.1/onts/status?community=komunitas_lain"
  ```

### Get Single ONT Status

Mengambil status dari satu ONT spesifik berdasarkan `ont_index` SNMP-nya.

- **Method:** `GET`
- **URL:** `/olt/{olt_ip}/ont/{ont_index}/status`

#### Parameters

- **Path Parameters:**
  - `olt_ip` (string, **required**): Alamat IP dari perangkat OLT.
  - `ont_index` (string, **required**): SNMP index dari ONT yang ingin dicek (contoh: `10101001`).
- **Query Parameter:**
  - `community` (string, *optional*): Community string SNMP yang ingin digunakan.

#### Contoh Penggunaan (cURL)

```bash
cURL -X GET "http://127.0.0.1:8000/olt/192.168.100.1/ont/10101001/status?community=jinomro"
```

#### Contoh Respons Sukses (`200 OK`)

```json
{
  "olt_ip": "192.168.100.1",
  "ont_index": "10101001",
  "status_code": 5,
  "status_text": "working"
}
```

### Get ONT Status by Description

Mengambil status dari satu ONT spesifik dengan cara mencarinya berdasarkan **Deskripsi** (format CLI Telnet).

**Catatan Penting:** Endpoint ini akan lebih lambat dibandingkan pencarian via `ont_index`, karena ia harus melakukan SNMP Walk ke semua ONT untuk menemukan Deskripsi yang cocok terlebih dahulu.

- **Method:** `GET`
- **URL:** `/olt/{olt_ip}/onts/by-description/{description}`

#### Parameters

- **Path Parameters:**
  - `olt_ip` (string, **required**): Alamat IP dari perangkat OLT.
  - `description` (string, **required**): Deskripsi dari ONT yang ingin dicari (contoh: `gpon-onu_1/2/3:1`).
- **Query Parameter:**
  - `community` (string, *optional*): Community string SNMP yang ingin digunakan.

#### Contoh Penggunaan (cURL)

```bash
cURL -X GET "http://127.0.0.1:8000/olt/192.168.100.1/onts/by-description/gpon-onu_1/2/3:1/status?community=jinomro"
```

#### Contoh Respons Sukses (`200 OK`)

```json
{
  "olt_ip": "192.168.100.1",
  "ont_index": "10101001",
  "status_code": 5,
  "status_text": "working"
}
```

### Get ONT Status by Name

Mengambil status dari satu ONT spesifik dengan cara mencarinya berdasarkan **Nama ONT**.

**Catatan Penting:** Endpoint ini juga akan lebih lambat karena memerlukan proses SNMP Walk.

- **Method:** `GET`
- **URL:** `/olt/{olt_ip}/onts/by-name/{ont_name}/status`

#### Parameters

- **Path Parameters:**
  - `olt_ip` (string, **required**): Alamat IP dari perangkat OLT.
  - `ont_name` (string, **required**): Nama dari ONT yang ingin dicari.
- **Query Parameter:**
  - `community` (string, *optional*): Community string SNMP yang ingin digunakan.

#### Contoh Penggunaan (cURL)

```bash
cURL -X GET "http://127.0.0.1:8000/olt/192.168.100.1/onts/by-name/NAMA_ONT_ANDA/status?community=jinomro"
```

#### Contoh Respons Sukses (`200 OK`)

```json
{
  "olt_ip": "192.168.100.1",
  "ont_index": "10101003",
  "status_code": 6,
  "status_text": "LOS"
}
```

### Get ONT Status by Serial Number (Hex)

Mengambil status dari satu ONT spesifik dengan cara mencarinya berdasarkan **Serial Number** dalam format Heksadesimal.

**Catatan Penting:** Endpoint ini juga akan lebih lambat karena memerlukan proses SNMP Walk.

- **Method:** `GET`
- **URL:** `/olt/{olt_ip}/onts/by-serial/{serial_number}/status`

#### Parameters

- **Path Parameters:**
  - `olt_ip` (string, **required**): Alamat IP dari perangkat OLT.
  - `serial_number` (string, **required**): Serial Number dari ONT dalam format Heksadesimal dan huruf besar (contoh: `FHTTA6798EFB`).
- **Query Parameter:**
  - `community` (string, *optional*): Community string SNMP yang ingin digunakan.

#### Contoh Penggunaan (cURL)

```bash
cURL -X GET "http://127.0.0.1:8000/olt/192.168.100.1/onts/by-serial/FHTTA6798EFB/status?community=jinomro"
```

#### Contoh Respons Sukses (`200 OK`)

```json
{
  "olt_ip": "192.168.100.1",
  "ont_index": "10101002",
  "status_code": 5,
  "status_text": "working"
}
```

#### Contoh Respons Sukses (`200 OK`)

Respon akan berisi alamat IP OLT dan sebuah array `data` yang berisi daftar ONT.

```json
{
  "olt_ip": "192.168.100.1",
  "data": [
    {
      "ont_index": "10101001",
      "status_code": 5,
      "status_text": "working"
    },
    {
      "ont_index": "10101002",
      "status_code": 5,
      "status_text": "working"
    },
    {
      "ont_index": "10101003",
      "status_code": 6,
      "status_text": "LOS"
    },
    {
      "ont_index": "10101004",
      "status_code": 8,
      "status_text": "DyingGasp"
    }
  ]
}
```

#### Contoh Respons Error

- **Jika OLT tidak dapat dijangkau atau timeout:** (`504 Gateway Timeout`)
  ```json
  {
    "detail": "SNMP request timed out."
  }
  ```

- **Jika terjadi error internal lain:** (`500 Internal Server Error`)
  ```json
  {
    "detail": "An unexpected error occurred: [pesan error]"
  }
  ```

### Dokumentasi Interaktif (Swagger)

FastAPI secara otomatis menyediakan dokumentasi interaktif. Setelah server berjalan, buka salah satu URL berikut di browser Anda:

- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

---

## Catatan untuk Produksi

Untuk penggunaan di lingkungan produksi yang perlu terhubung ke ratusan atau ribuan OLT, direkomendasikan untuk mengadopsi arsitektur yang lebih kuat:

1.  **Background Worker:** Pisahkan proses polling SNMP dari request API. Gunakan task queue seperti **Celery** untuk melakukan polling secara periodik di latar belakang.
2.  **Database:** Simpan hasil polling ke dalam sebuah database (misalnya InfluxDB untuk data time-series, atau PostgreSQL).
3.  **API Cepat:** Ubah endpoint API agar hanya membaca data terakhir dari database, bukan melakukan polling langsung ke perangkat.

Pendekatan ini membuat API lebih cepat, andal, dan skalabel.