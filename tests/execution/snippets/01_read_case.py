# Step 1: Read mesh file.
import os

MESH_FILE = r"E:\Code_MCP\ion\ion-main\mixing_elbow.msh.h5"

if not os.path.isfile(MESH_FILE):
    raise FileNotFoundError(f"Mesh file not found: {MESH_FILE}")

solver.settings.file.read_case(file_name=MESH_FILE)

_result = {"step": "read-case", "mesh_file": MESH_FILE, "ok": True}
