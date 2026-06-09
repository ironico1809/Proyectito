import os
import sys
import time
import requests
import psycopg2
from dotenv import load_dotenv

# Path to the .env file in the same backend folder
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")
API_URL = "http://127.0.0.1:8000"

def get_auth_token():
    try:
        url = f"{API_URL}/auth/login"
        payload = {
            "email": "juan@gmail.com",
            "password": "123456"
        }
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            return res.json()["access_token"]
        else:
            print("[ERROR] Login failed:", res.text)
    except Exception as e:
        print("[ERROR] Login exception:", e)
    return None

def get_latest_incident():
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found in .env")
        return None

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_incidente, latitud_emergencia, longitud_emergencia, estado_enum, tecnico_id
            FROM incidentes
            ORDER BY id_incidente DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return {
                "id_incidente": row[0],
                "lat_emergencia": float(row[1]) if row[1] is not None else -17.7833,
                "lng_emergencia": float(row[2]) if row[2] is not None else -63.1821,
                "estado": str(row[3]),
                "tecnico_id": row[4]
            }
        else:
            print("No incidents found in the database.")
            return None
    except Exception as e:
        print("Database query failed:", e)
        return None
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def get_incident_by_id(incident_id):
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found in .env")
        return None

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_incidente, latitud_emergencia, longitud_emergencia, estado_enum, tecnico_id
            FROM incidentes
            WHERE id_incidente = %s
        """, (incident_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id_incidente": row[0],
                "lat_emergencia": float(row[1]) if row[1] is not None else -17.7833,
                "lng_emergencia": float(row[2]) if row[2] is not None else -63.1821,
                "estado": str(row[3]),
                "tecnico_id": row[4]
            }
        else:
            print(f"Incident #{incident_id} not found in the database.")
            return None
    except Exception as e:
        print("Database query failed:", e)
        return None
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def update_status_api(incident_id, token, status, costo_final=None):
    url = f"{API_URL}/incidentes/{incident_id}/estado"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "estado_enum": status,
        "costo_final": costo_final,
        "comentario": f"Actualizado por simulador a {status}"
    }
    try:
        res = requests.put(url, json=payload, headers=headers, timeout=5)
        if res.status_code == 200:
            print(f"[SUCCESS] Incident status updated to '{status}' via API!")
            return True
        else:
            print(f"[ERROR] Failed to update status to '{status}'. Status: {res.status_code}, Response: {res.text}")
    except Exception as e:
        print(f"[ERROR] Status update to '{status}' exception:", e)
    return False

def simulate_route(incident_id=None):
    # 1. Get Auth Token
    token = get_auth_token()
    if not token:
        print("Could not retrieve authentication token. Aborting simulation.")
        return

    # 2. Get incident
    if incident_id:
        incident = get_incident_by_id(incident_id)
    else:
        incident = get_latest_incident()

    if not incident:
        print("No incident found to simulate.")
        return

    print("=" * 60)
    print(f"SIMULATOR: Found Incident #{incident['id_incidente']}")
    print(f"Status: {incident['estado']}")
    print(f"Emergency coordinates: {incident['lat_emergencia']}, {incident['lng_emergencia']}")
    print(f"Technician ID assigned: {incident['tecnico_id']}")
    print("=" * 60)

    # Start coordinates (offset by 0.012 degrees ~ 1.3 km)
    start_lat = incident['lat_emergencia'] + 0.012
    start_lng = incident['lng_emergencia'] - 0.012

    steps = 10
    print(f"Simulating technician moving in {steps} steps...")
    
    for i in range(steps + 1):
        fraction = i / steps
        # Linear interpolation from start to emergency location
        current_lat = start_lat + (incident['lat_emergencia'] - start_lat) * fraction
        current_lng = start_lng + (incident['lng_emergencia'] - start_lng) * fraction
        
        print(f"\nStep {i}/{steps} - Technician Coordinates: {current_lat:.6f}, {current_lng:.6f}")
        
        # Send update to backend via HTTP PUT
        payload = {
            "latitud": current_lat,
            "longitud": current_lng
        }
        
        url = f"{API_URL}/incidentes/{incident['id_incidente']}/ubicacion-tecnico"
        try:
            res = requests.put(url, json=payload, timeout=5)
            if res.status_code == 200:
                print("[SUCCESS] Location update sent to API successfully! (Broadcast triggered)")
            else:
                print(f"[ERROR] Failed to update location. Status: {res.status_code}, Response: {res.text}")
        except Exception as e:
            print("[ERROR] API request exception:", e)

        # Sleep between updates (e.g. 1 second)
        if i < steps:
            print("Waiting 1 second before next update...")
            time.sleep(1)

    print("\nSimulation: Technician has reached the emergency site!")
    
    # 3. Update status to 'en_atencion'
    print("Updating incident status to 'en_atencion'...")
    update_status_api(incident['id_incidente'], token, "en_atencion")
    
    # 4. Wait 4 seconds (simulating work)
    print("Waiting 4 seconds (simulating technician working)...")
    time.sleep(4)
    
    # 5. Update status to 'finalizado' and set final cost
    print("Updating incident status to 'finalizado' with cost Bs. 150.0...")
    update_status_api(incident['id_incidente'], token, "finalizado", costo_final=150.0)

    print("\nSimulation complete! Technician reached the destination, attended the vehicle, and finalized the service.")

if __name__ == "__main__":
    inc_id = None
    if len(sys.argv) > 1:
        try:
            inc_id = int(sys.argv[1])
        except ValueError:
            print(f"Invalid incident ID format: '{sys.argv[1]}'. Using latest incident instead.")
    simulate_route(inc_id)
