from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


project_root = Path(SPECPATH)
frontend_dist = project_root / "xwzx-news" / "dist"
if not (frontend_dist / "index.html").is_file():
    raise FileNotFoundError("请先执行 npm run build:demo 生成前端 dist")

hiddenimports = (
    collect_submodules("sqlalchemy.dialects.sqlite")
    + collect_submodules("passlib.handlers")
    + ["aiosqlite", "bcrypt", "h11"]
)

a = Analysis(
    [str(project_root / "demo_launcher.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(frontend_dist), "web")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FastApiVueNews",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="FastApiVueNews",
)
