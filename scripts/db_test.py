import psycopg2
import sys
import os
from datetime import datetime

# Add project root to python path to import settings
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
from app.config import settings

try:
    conn = psycopg2.connect(settings.DATABASE_URL)

    cur = conn.cursor()

    cur.execute("SELECT NOW(), NOW() at time zone 'UTC'")
    now_res = cur.fetchone()
    print("DB NOW():", now_res[0], " | DB NOW(UTC):", now_res[1])

    cur.execute("SELECT device_uid, last_seen FROM vehicles")
    vehicles = cur.fetchall()
    print("VEHICLES:")
    for v in vehicles:
        print(v)

    cur.execute("SELECT count(*) FROM vehicles WHERE last_seen >= (NOW() at time zone 'UTC' - interval '5 minutes')")
    online = cur.fetchone()[0]
    print("ONLINE IN DB (UTC based):", online)

except Exception as e:
    print("ERROR:", e)
