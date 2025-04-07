# Utvecklingsguide för EON Bot Launcher

Den här guiden är avsedd för den som vill bygga och distribuera EON Bot Launcher.

## Förutsättningar

För att bygga EON Bot Launcher behöver du:

1. Python 3.8 eller senare installerat
2. Följande Python-paket installerade:
   ```
   pip install PyQt5 PyInstaller
   ```

## Bygga EXE-filen

1. Öppna en kommandotolk och navigera till denna mapp (`C:\temp\ai\diceroller\launcher`)
2. Kör byggskriptet:
   ```
   python build_exe.py
   ```
3. Om allt går bra skapas en mapp `dist\EONBotLauncher` som innehåller den körbara filen och alla nödvändiga filer

## Distribuera till användare

Det finns ett par olika sätt att distribuera programmet:

### Alternativ 1: Zippa och skicka
1. Zippa hela mappen `dist\EONBotLauncher`
2. Inkludera `INSTALLATION_GUIDE.md` för att hjälpa användaren att komma igång
3. Skicka zip-filen till användaren
4. Användaren packar upp zip-filen och kan direkt köra programmet

### Alternativ 2: Skapa en installationsfil
För en mer professionell distribution kan du skapa en installationsfil:

1. Ladda ner och installera [Inno Setup](https://jrsoftware.org/isdl.php)
2. Skapa ett nytt skript i Inno Setup och konfigurera det att:
   - Installera innehållet i `dist\EONBotLauncher`
   - Skapa genvägar i Startmenyn och/eller på skrivbordet
   - Inkludera dokumentationen
3. Bygg installationsfilen och distribuera den till användaren

## Anpassning

Du kan anpassa launchen på följande sätt:

- **Utseende:** Redigera `setup_style()` i `eon_bot_launcher.py` för att ändra färger och stil
- **Hjälptext:** Uppdatera HTML i `setup_help_tab()` för att anpassa hjälpinformationen
- **Standardvärden:** Ändra förinställda värden som Pinecone Index-namn

## Felsökning vid byggande

Om du stöter på problem vid byggande:

1. **Saknade paket:** Se till att alla nödvändiga Python-paket är installerade
2. **Saknad ikon:** Skapa eller ladda ner en icon.ico-fil och placera den i denna mapp
3. **Problem med PyInstaller:** Försök med att köra PyInstaller direkt:
   ```
   pyinstaller eon_bot_launcher.py --name=EONBotLauncher --onedir --windowed
   ```

## Anteckningar om säkerhet

- API-nycklar lagras i en JSON-fil på användarens dator
- Alla nycklar visas som lösenordsinmatning (*****) för att skydda dem från visuell inspektion
- För ökad säkerhet, överväg att implementera kryptering av den lagrade konfigurationsfilen