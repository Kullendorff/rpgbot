import os
import PyInstaller.__main__
import shutil
import sys

# Ställ in arbetskatalog till samma katalog som skriptet
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Skapa dist- och build-mappar om de inte redan finns
os.makedirs('dist', exist_ok=True)
os.makedirs('build', exist_ok=True)

# Rensa eventuella tidigare byggen
if os.path.exists('dist/EONBotLauncher'):
    shutil.rmtree('dist/EONBotLauncher')

print("Bygger EON Bot Launcher med PyInstaller...")

# Kör PyInstaller
PyInstaller.__main__.run([
    'eon_bot_launcher.py',                     # Sökväg till huvudskriptet
    '--name=EONBotLauncher',                   # Namn på programmet
    '--onedir',                                # Skapa en mapp istället för en enda fil
    '--windowed',                              # Inget konsolfönster
    '--add-data=README.md;.',                  # Inkludera README-filen
    '--icon=icon.ico',                         # Ikonfil (skapa eller ladda ner en passande ikon)
    '--clean',                                 # Rensa cache före byggande
    '--noupx',                                 # Inget UPX (kan orsaka problem)
    '--hidden-import=PyQt5',
    '--hidden-import=PyQt5.QtCore',
    '--hidden-import=PyQt5.QtGui',
    '--hidden-import=PyQt5.QtWidgets'
])

print("Bygge slutfört!")
print("EXE-filen finns i mappen: dist/EONBotLauncher")