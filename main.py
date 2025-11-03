from fastapi import FastAPI, HTTPException
import aiosnmp
import asyncio
import os

app = FastAPI()

# --- Konfigurasi & Konstanta ---
SNMP_COMMUNITY = os.getenv('SNMP_COMMUNITY_STRING', 'public')
ONT_STATUS_OID = '.1.3.6.1.4.1.3902.1012.3.28.2.1.4'
ONT_DESC_OID = '.1.3.6.1.4.1.3902.1012.3.28.1.1.3'
# OID untuk Nama ONT yang diberikan oleh user
ONT_NAME_OID = '.1.3.6.1.4.1.3902.1012.3.28.1.1.2'

STATUS_MAP = {
    1: "LOS",
    3: "Working",
    4: "DyingGasp",
}

# --- Fungsi Helper ---
async def get_all_onts_status(olt_ip: str, community_string: str):
    ont_data = []
    try:
        async with aiosnmp.Snmp(host=olt_ip, port=161, community=community_string, timeout=5) as snmp:
            async for varbind in await snmp.walk(ONT_STATUS_OID):
                oid = str(varbind.oid)
                value = varbind.value
                value = int(value)
                ont_index = oid.split(f"{ONT_STATUS_OID}.")[1]
                status_text = STATUS_MAP.get(value, "unknown")
                ont_data.append({
                    "ont_index": ont_index,
                    "status_code": value,
                    "status_text": status_text
                })
    except Exception as e:
        raise HTTPException(status_code=504, detail=f"SNMP Error: {e}")
    return ont_data

async def find_ont_index_by_description(olt_ip: str, community_string: str, description: str):
    try:
        async with aiosnmp.Snmp(host=olt_ip, port=161, community=community_string, timeout=10) as snmp:
            results = await snmp.walk(ONT_DESC_OID)
            for varbind in results:
                oid = str(varbind.oid)
                value = varbind.value
                desc_from_device = value.decode('ascii', errors='ignore').strip()
                if desc_from_device == description:
                    return oid.split(f"{ONT_DESC_OID}.")[1]
    except Exception as e:
        raise HTTPException(status_code=504, detail=f"SNMP Error while searching description: {e}")
    return None

async def find_ont_index_by_name(olt_ip: str, community_string: str, ont_name: str):
    try:
        async with aiosnmp.Snmp(host=olt_ip, port=161, community=community_string, timeout=10) as snmp:
            results = await snmp.walk(ONT_NAME_OID)
            for varbind in results:
                oid = str(varbind.oid)
                value = varbind.value
                name_from_device = value.decode('ascii', errors='ignore').strip()
                if name_from_device == ont_name:
                    return oid.split(f"{ONT_NAME_OID}.")[1]
    except Exception as e:
        raise HTTPException(status_code=504, detail=f"SNMP Error while searching name: {e}")
    return None

# --- Endpoint API ---
@app.get("/olt/{olt_ip}/onts/status")
async def get_onts_status_endpoint(olt_ip: str, community: str | None = None):
    community_to_use = community if community else SNMP_COMMUNITY
    ont_statuses = await get_all_onts_status(olt_ip, community_to_use)
    return {"olt_ip": olt_ip, "data": ont_statuses}

@app.get("/olt/{olt_ip}/ont/{ont_index}/status")
async def get_single_ont_status_endpoint(olt_ip: str, ont_index: str, community: str | None = None):
    community_to_use = community if community else SNMP_COMMUNITY
    full_oid = f"{ONT_STATUS_OID}.{ont_index}"
    try:
        async with aiosnmp.Snmp(host=olt_ip, port=161, community=community_to_use, timeout=5) as snmp:
            result = await snmp.get(full_oid)
            if not result:
                raise HTTPException(status_code=404, detail="OID not found or no response")
            
            # Perbaikan di sini: akses .value dari objek result
            value = result[0].value
            status_code = int(value)
            status_text = STATUS_MAP.get(status_code, "unknown")
            return {"olt_ip": olt_ip, "ont_index": ont_index, "status_code": status_code, "status_text": status_text}
    except Exception as e:
        raise HTTPException(status_code=504, detail=f"SNMP Error: {e}")

@app.get("/olt/{olt_ip}/onts/by-description/{description}")
async def get_ont_status_by_desc_endpoint(olt_ip: str, description: str, community: str | None = None):
    community_to_use = community if community else SNMP_COMMUNITY
    ont_index = await find_ont_index_by_description(olt_ip, community_to_use, description)
    if not ont_index:
        raise HTTPException(status_code=404, detail=f"ONT with description '{description}' not found.")
    return await get_single_ont_status_endpoint(olt_ip, ont_index, community_to_use)

@app.get("/olt/{olt_ip}/onts/by-name/{ont_name}/status")
async def get_ont_status_by_name_endpoint(olt_ip: str, ont_name: str, community: str | None = None):
    community_to_use = community if community else SNMP_COMMUNITY
    ont_index = await find_ont_index_by_name(olt_ip, community_to_use, ont_name)
    if not ont_index:
        raise HTTPException(status_code=404, detail=f"ONT with name '{ont_name}' not found.")
    return await get_single_ont_status_endpoint(olt_ip, ont_index, community_to_use)
