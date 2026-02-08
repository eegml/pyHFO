"""
macOS py2app packaging script (not used for standard Python packaging).

For standard installation, use: pip install -e .

Usage (macOS .app bundle only):
    python setup_macos.py py2app
"""

from setuptools import setup
import sys
import os
sys.setrecursionlimit(1500)
APP = ['main.py']
DATA_FILES = []
for folder in ['pyhfo2app', 'ckpt']:
    for root, dirs, files in os.walk(folder):
        for file in files:
            DATA_FILES.append((root, [os.path.join(root, file)]))
print(DATA_FILES)

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'pyhfo2app/ui/images/icon1.icns',
    'packages': [
        'matplotlib',
        'mne',
        'numpy',
        'p_tqdm',
        'pandas',
        'openpyxl',
        'pyqt5',  # Uncomment this if PyQt5 is a dependency
        #'PyQt5_sip',
        'pyqtgraph',
        'scipy',
        #'scikit-image',
        # 'torch',
        # 'torchvision',
        'xy'
        "chardet",
        'tqdm',
        'ctypes'
    ],
    'includes': ['liblzma'],
    #'frameworks': ['/Users/yipengzhang/miniconda3/lib/liblzma.5.dylib'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=['torch','torchvision'],
)
