import os
import sys
import subprocess

# Change working directory to project root
project_root = r"E:\Embedded Projects\GPS_Project"
os.chdir(project_root)
print(f"[run_alembic.py] Changed directory to: {os.getcwd()}")

# Run alembic command using virtualenv python
cmd = [
    r"venv\Scripts\python.exe",
    "-m", "alembic"
] + sys.argv[1:]

print(f"[run_alembic.py] Running command: {' '.join(cmd)}")
res = subprocess.run(cmd)
sys.exit(res.returncode)
