from fastapi import FastAPI, HTTPException
from pysnmp.hlapi.asyncio import *
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
async def get_ont_status(olt_ip: str):
    """
    Menjalankan snmpwalk ke OLT untuk mendapatkan status semua ONT.
    Menggunakan pysnmp asynchronous untuk performa tinggi.
    """
    ont_data = []
    
    # Inisialisasi SNMP Engine. Ini adalah objek utama untuk semua operasi SNMP.
    snmpEngine = SnmpEngine()

    # Melakukan snmpwalk secara asynchronous.
    # nextCmd adalah fungsi low-level yang setara dengan 'walk'.
    # Kita iterasi (await for) hasilnya satu per satu saat diterima dari network.
    try:
        async for (errorIndication,
                     errorStatus,
                     errorIndex,
                     varBinds) in nextCmd(snmpEngine,
                                          CommunityData(SNMP_COMMUNITY, mpModel=0),
                                          UdpTransportTarget((olt_ip, 161), timeout=1.0, retries=5),
                                          ContextData(),
                                          ObjectType(ObjectIdentity(ONT_STATUS_OID)),
                                          lexicographicMode=False):

            # --- Penanganan Error SNMP ---
            if errorIndication:
                # Error pada transport layer (misal: host tidak terjangkau)
                raise HTTPException(status_code=504, detail=f"SNMP request failed: {errorIndication}")
            elif errorStatus:
                # Error pada level PDU SNMP (misal: noSuchName)
                # Pesan error ini biasanya cukup teknis.
                raise HTTPException(status_code=500, detail=f"SNMP error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}")

            # --- Parsing Hasil ---
            # varBinds adalah list of tuple, biasanya berisi satu tuple untuk walk
            for varBind in varBinds:
                # varBind[0] adalah OID, varBind[1] adalah value
                oid = str(varBind[0])
                value = int(varBind[1])

                # Ambil bagian terakhir dari OID sebagai ont_index
                # Contoh OID: .1.3.6.1.4.1.3902.1012.3.28.2.1.4.10101001
                # Kita split berdasarkan OID awal untuk mendapatkan index-nya.
                ont_index = oid.split(f"{ONT_STATUS_OID}.")[1]
                
                # Terjemahkan status code ke teks
                status_text = STATUS_MAP.get(value, "unknown")

                ont_data.append({
                    "ont_index": ont_index,
                    "status_code": value,
                    "status_text": status_text
                })

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="SNMP request timed out.")
    except Exception as e:
        # Menangkap error lain yang mungkin terjadi
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        # Pastikan transport ditutup setelah selesai atau jika terjadi error
        snmpEngine.transportDispatcher.closeDispatcher()


    return ont_data


# --- Endpoint API ---
@app.get("/olt/{olt_ip}/onts/status")
async def get_onts_status_endpoint(olt_ip: str):
    """
    Endpoint untuk mendapatkan status semua ONT dari sebuah OLT ZTE.
    """
    ont_statuses = await get_ont_status(olt_ip)
    
    return {
        "olt_ip": olt_ip,
        "data": ont_statuses
    }

# --- Untuk menjalankan aplikasi (gunakan uvicorn) ---
# Command: uvicorn main:app --reload
# Contoh URL: http://127.0.0.1:8000/olt/192.168.1.1/onts/status
