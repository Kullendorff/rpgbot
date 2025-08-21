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

echo Startar Python-skript... >> %LOGFILE% 2>&1
:: Starta boten och skicka all output (både vanlig och fel) till loggfilen
python -u src\main.py >> %LOGFILE% 2>&1