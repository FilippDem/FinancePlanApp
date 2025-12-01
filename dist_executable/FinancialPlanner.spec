# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher.py'],  # Use launcher as entry point
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),  # Include assets folder
        ('FinancialPlanner_v0_85.py', '.'),  # Include main app as data file
    ],
    hiddenimports=[
        # Streamlit core
        'streamlit',
        'streamlit.web.cli',
        'streamlit.web.bootstrap',
        'streamlit.runtime.scriptrunner.magic_funcs',
        'streamlit.runtime.scriptrunner.script_runner',
        'streamlit.runtime.state',
        'streamlit.runtime.state.session_state',
        'streamlit.runtime.media_file_manager',
        'streamlit.runtime.caching',
        'streamlit.runtime.uploaded_file_manager',
        'streamlit.elements',
        'streamlit.components.v1',
        # Data processing
        'pandas',
        'pandas.io.formats.style',
        'numpy',
        'numpy.random',
        # Plotting
        'plotly',
        'plotly.graph_objects',
        'plotly.express',
        'plotly.subplots',
        'plotly.io',
        # File handling
        'openpyxl',
        'openpyxl.workbook',
        'openpyxl.styles',
        # PDF generation
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.lib.units',
        'reportlab.platypus',
        'reportlab.lib.colors',
        'reportlab.pdfgen',
        'reportlab.pdfgen.canvas',
        # Chart rendering
        'kaleido',
        # GUI
        'tkinter',
        'tkinter.filedialog',
        # Additional dependencies
        'altair',
        'click',
        'validators',
        'tornado',
        'tornado.web',
        'tornado.websocket',
        'tornado.ioloop',
        'watchdog',
        'watchdog.observers',
        # Standard library modules that might need explicit inclusion
        'queue',
        'asyncio',
        'concurrent.futures',
        'PIL',
        'PIL.Image',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FinancialPlanner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to True to see any error messages
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # You can add an icon file here if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FinancialPlanner',
)
