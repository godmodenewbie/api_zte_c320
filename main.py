from fastapi import FastAPI, HTTPException
from pysnmp.asyncio import snmpwalk
from pysnmp.error import PySnmpError
import asyncio
import os

app = FastAPI()

# --- Konfigurasi & Konstanta ---
# Membaca community string dari environment variable 'SNMP_COMMUNITY_STRING'.
# Jika tidak diset, akan menggunakan 'public' sebagai default.
SNMP_COMMUNITY = os.getenv('SNMP_COMMUNITY_STRING', 'public')
ONT_STATUS_OID = '.1.3.6.1.4.1.3902.1012.3.28.2.1.4'

STATUS_MAP = {
    5: "working",
    6: "LOS",
    8: "DyingGasp",
}

# --- Fungsi Helper ---
async def get_ont_status(olt_ip: str, community_string: str):
    """
    Menjalankan snmpwalk ke OLT untuk mendapatkan status semua ONT.
    Menggunakan API pysnmp.asyncio.snmpwalk yang modern dan stabil.
    """
    ont_data = []
    try:
        # snmpwalk adalah generator asynchronous tingkat tinggi yang menyederhanakan proses.
        async for varBind in snmpwalk(community_string, olt_ip, 161, ONT_STATUS_OID):
            oid, value = varBind
            oid = str(oid)
            value = int(value)

            # Ambil bagian terakhir dari OID sebagai ont_index
            ont_index = oid.split(f"{ONT_STATUS_OID}.")[1]
            
            # Terjemahkan status code ke teks
            status_text = STATUS_MAP.get(value, "unknown")

            ont_data.append({
                "ont_index": ont_index,
                "status_code": value,
                "status_text": status_text
            })

    except PySnmpError as e:
        # Menangani error spesifik dari SNMP (misal: timeout, host tidak ditemukan)
        raise HTTPException(status_code=504, detail=f"SNMP Error: {e}")
    except Exception as e:
        # Menangani error tak terduga lainnya (misal: saat parsing)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    return ont_data


    return ont_data


# --- Endpoint API ---
@app.get("/olt/{olt_ip}/onts/status")
async def get_onts_status_endpoint(olt_ip: str, community: str | None = None):
    """
    Endpoint untuk mendapatkan status semua ONT dari sebuah OLT ZTE.

    Anda bisa menyediakan community string spesifik via query parameter `?community=...`
    Jika tidak disediakan, nilai default akan digunakan (dari env var `SNMP_COMMUNITY_STRING`).
    """
    # Tentukan community string yang akan digunakan:
    # 1. Dari query parameter `community`, jika ada.
    # 2. Jika tidak, dari environment variable `SNMP_COMMUNITY`.
    community_to_use = community if community else SNMP_COMMUNITY

    ont_statuses = await get_ont_status(olt_ip, community_to_use)
    
    return {
        "olt_ip": olt_ip,
        "data": ont_statuses
    }

# --- Untuk menjalankan aplikasi (gunakan uvicorn) ---
# Command: uvicorn main:app --reload
# Contoh URL: http://127.0.0.1:8000/olt/192.168.1.1/onts/status
