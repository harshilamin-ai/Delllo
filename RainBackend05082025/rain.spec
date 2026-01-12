
# rain_patched.spec
# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules

# Path to your main.py entry point
script_path = os.path.join(os.getcwd(), "main.py")

# Collect all hidden imports for required packages
hiddenimports = []
hiddenimports += collect_submodules("fastapi")
hiddenimports += collect_submodules("starlette")
hiddenimports += collect_submodules("pydantic")
hiddenimports += collect_submodules("jinja2")
hiddenimports += collect_submodules("uvicorn")
hiddenimports += collect_submodules("uvloop")
hiddenimports += collect_submodules("httptools")
hiddenimports += collect_submodules("celery")
hiddenimports += collect_submodules("redis")
hiddenimports += ["psycopg2"]
hiddenimports += collect_submodules("tinydb")
hiddenimports += collect_submodules("langchain")
hiddenimports += collect_submodules("faiss")
hiddenimports += collect_submodules("sklearn")
hiddenimports += collect_submodules("numpy")

# Include data folder contents
datas = []
for root, dirs, files in os.walk("data"):
    for file in files:
        src = os.path.join(root, file)
        dst = os.path.join("data", os.path.relpath(root, "data"))
        datas.append((src, dst))

# Include prompt_templates.py if used
datas.append(("prompt_templates.py", "."))

# No extra binaries by default; add specific binaries here if needed
binaries = []

a = Analysis(
    [script_path],
    pathex=[os.getcwd()],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="rain_server",
    debug=False,
    strip=False,
    upx=True,
    console=True,
)
