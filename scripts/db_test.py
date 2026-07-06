import psycopg2
from datetime import datetime

try:
    conn = psycopg2.connect("postgresql://postgres:postgres123@127.0.0.1:5432/vts_db")
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
