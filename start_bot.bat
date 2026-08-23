@echo off
:: Sätter en loggfil i samma mapp som skriptet
set LOGFILE="C:\Diceroller\bot_run.log"

:: Rensa gammal logg och skriv starttid
echo =================================== > %LOGFILE%
echo       Startar bot-skript: %date% %time%      >> %LOGFILE%
echo =================================== >> %LOGFILE%

:: Ändra till mappen där ditt projekt ligger. Alla fel och meddelanden skickas till loggfilen.
cd /d "C:\Diceroller" >> %LOGFILE% 2>&1

echo Aktiverar virtuell miljö... >> %LOGFILE% 2>&1
:: Aktivera den virtuella miljön
call .\venv\Scripts\activate.bat >> %LOGFILE% 2>&1

:: FAIL-LOUD: avbryt om aktiveringen misslyckades i stället för att tyst
:: falla igenom till system-Python (kan sakna beroenden eller ha fel versioner).
if errorlevel 1 (
    echo FEL: Kunde inte aktivera .\venv\Scripts\activate.bat - avbryter. >> %LOGFILE%
    echo FEL: Aterskapa miljoen: py -3.13 -m venv venv && venv\Scripts\pip install -r requirements.txt >> %LOGFILE%
    exit /b 1
)

:: Dubbelkolla att venv-python verkligen finns (aktiveringen kan "lyckas" tom)
if not exist ".\venv\Scripts\python.exe" (
    echo FEL: .\venv\Scripts\python.exe saknas - venv ar trasig eller ej skapad. Avbryter. >> %LOGFILE%
    echo FEL: Aterskapa miljoen: py -3.13 -m venv venv && venv\Scripts\pip install -r requirements.txt >> %LOGFILE%
    exit /b 1
)

echo Startar Python-skript... >> %LOGFILE% 2>&1
:: Starta boten och skicka all output (både vanlig och fel) till loggfilen
python -u src\main.py >> %LOGFILE% 2>&1
