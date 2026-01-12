# RAINBackend_patched.spec
# -*- mode: python -*-

import os
import llama_cpp
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# ------------------------------------------------------------------------------
# 1) ENTRY SCRIPT
script = "main.py"

# ------------------------------------------------------------------------------
# 2) HIDDEN IMPORTS (ensure PyInstaller pulls in all subpackages)
hiddenimports = []
hiddenimports += collect_submodules("fastapi")
hiddenimports += collect_submodules("starlette")
hiddenimports += collect_submodules("pydantic")
hiddenimports += collect_submodules("jinja2")
hiddenimports += collect_submodules("uvicorn")
hiddenimports += collect_submodules("uvicorn.main")
hiddenimports += collect_submodules("uvicorn.supervisors")
hiddenimports += collect_submodules("uvicorn.protocols")
hiddenimports += collect_submodules("uvloop")
hiddenimports += collect_submodules("httptools")
hiddenimports += collect_submodules("anyio")
hiddenimports += collect_submodules("yaml")
hiddenimports += collect_submodules("markupsafe")
hiddenimports += collect_submodules("cffi")
hiddenimports += collect_submodules("cryptography")
hiddenimports += collect_submodules("cryptography.hazmat.backends.openssl.backend")
hiddenimports += collect_submodules("h11")
hiddenimports += collect_submodules("click")
hiddenimports += collect_submodules("jinja2.ext")

# Make sure llama_cpp’s Python code is pulled in
hiddenimports += collect_submodules("llama_cpp")
hiddenimports += collect_submodules("apscheduler")
hiddenimports += collect_submodules("apscheduler.schedulers")

# ------------------------------------------------------------------------------
# 3) DATA FILES (Python packages with templates, plus your own data/ folder)
datas = []

# FastAPI, Jinja2, Starlette, Pydantic, Uvicorn non-code files:
datas += collect_data_files("fastapi")
datas += collect_data_files("jinja2")
datas += collect_data_files("starlette")
datas += collect_data_files("pydantic")
datas += collect_data_files("uvicorn")
datas += collect_data_files("apscheduler")

# Your own “data/” folder → keep the same relative tree under dist/rain_server/data
for root, dirs, files in os.walk("data"):
    for fname in files:
        src_path = os.path.join(root, fname)
        rel_dir = os.path.relpath(root, "data")  # e.g. if root="data\sub", rel_dir="sub"
        dst_dir = os.path.join("data", rel_dir)   # place under dist/rain_server/data/sub
        datas.append((src_path, dst_dir))

# Include prompt_templates.py at top‐level of the bundle
datas.append(("prompt_templates.py", "."))

# ------------------------------------------------------------------------------
# 4) Bundle llama_cpp/lib/*.dll  → we walk the real folder on disk:
llama_pkg_dir = os.path.dirname(llama_cpp.__file__)
llama_lib_dir = os.path.join(llama_pkg_dir, "lib")

if os.path.isdir(llama_lib_dir):
    for dll_name in os.listdir(llama_lib_dir):
        src_dll = os.path.join(llama_lib_dir, dll_name)
        # preserve “llama_cpp/lib” under the bundle:
        datas.append((src_dll, os.path.join("llama_cpp", "lib")))

# ------------------------------------------------------------------------------
# 5) STANDARD PYINSTALLER SETUP

block_cipher = None

a = Analysis(
    [script],
    pathex=[os.getcwd()],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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

# ---------------------------
# THIS “COLLECT” IS CRUCIAL → forces a one‐dir build
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="rain_server",
)
