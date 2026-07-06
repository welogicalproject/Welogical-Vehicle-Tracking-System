import os
import sys
import psycopg2
from alembic.config import Config
from alembic import command

PROJECT_ROOT = r"E:\Embedded Projects\GPS_Project"
os.chdir(PROJECT_ROOT)
print(f"[db_validate.py] Changed directory to: {os.getcwd()}")

# 1. Run Alembic upgrade head programmatically
try:
    print("[db_validate.py] Running Alembic upgrade head...")
    alembic_cfg = Config(os.path.join(PROJECT_ROOT, "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
    print("[db_validate.py] Alembic upgrade head executed successfully!")
except Exception as e:
    print(f"[db_validate.py] ERROR during Alembic upgrade: {e}")
    sys.exit(1)

# 2. Connect to database and verify table existence
try:
    print("[db_validate.py] Connecting to PostgreSQL to check tables...")
    conn = psycopg2.connect("postgresql://postgres:postgres123@127.0.0.1:5432/vts_db")
    cur = conn.cursor()
    
    # Query tables in public schema
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]
    print(f"[db_validate.py] Found tables in database: {tables}")
    
    required_tables = ["events", "device_configs", "device_commands", "command_logs"]
    missing = [t for t in required_tables if t not in tables]
    
    if not missing:
        print("[db_validate.py] SUCCESS: All VTS Phase 1 and 2 tables are verified to exist!")
    else:
        print(f"[db_validate.py] FAILURE: Missing tables: {missing}")
        sys.exit(1)
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"[db_validate.py] ERROR connecting to database: {e}")
    sys.exit(1)
