# Installationsguide för EON Diceroller Bot

Denna guide hjälper dig att komma igång med EON Diceroller Bot utan tekniska förkunskaper.

## Steg 1: Skaffa nödvändiga API-nycklar

### Discord Token
1. Gå till [Discord Developer Portal](https://discord.com/developers/applications)
2. Klicka på "New Application" uppe till höger
3. Ge din applikation ett namn (t.ex. "EON Bot") och klicka på "Create"
4. Gå till "Bot" i vänstermenyn
5. Klicka på "Add Bot" och bekräfta genom att klicka på "Yes, do it!"
6. Under "TOKEN", klicka på "Copy" för att kopiera din bot-token
7. Kom ihåg att aktivera följande inställningar:
   - MESSAGE CONTENT INTENT (under "Privileged Gateway Intents")
   - PRESENCE INTENT (under "Privileged Gateway Intents")
   - SERVER MEMBERS INTENT (under "Privileged Gateway Intents")
8. Spara inställningarna
9. Gå till "OAuth2" → "URL Generator" i vänstermenyn
10. Kryssa i "bot" under "SCOPES" och välj följande behörigheter under "BOT PERMISSIONS":
    - Read Messages/View Channels
    - Send Messages
    - Send Messages in Threads
    - Embed Links
    - Attach Files
    - Read Message History
    - Use External Emojis
    - Add Reactions
11. Kopiera den genererade URL:en längst ner och öppna den i en webbläsare
12. Välj den Discord-server där du vill lägga till boten och klicka på "Authorize"

### Pinecone API-nyckel
1. Gå till [Pinecone](https://app.pinecone.io/) och skapa ett konto om du inte redan har ett
2. Efter inloggning, gå till "API Keys" eller liknande sektion
3. Kopiera din API-nyckel

### Anthropic Claude API-nyckel
1. Gå till [Anthropic Console](https://console.anthropic.com/) och skapa ett konto
2. Efter inloggning, gå till "API Keys" eller liknande sektion
3. Skapa en ny API-nyckel och kopiera den

### OpenAI API-nyckel
1. Gå till [OpenAI Platform](https://platform.openai.com/) och skapa ett konto
2. Efter inloggning, gå till "API keys" i din kontoprofil
3. Klicka på "Create new secret key" och kopiera den nya nyckeln

## Steg 2: Starta EON Bot Launcher

1. Öppna EON Bot Launcher genom att dubbelklicka på "EONBotLauncher.exe"
2. Fyll i alla API-nycklar i respektive fält:
   - Discord Token
   - Pinecone API-nyckel
   - Anthropic Claude API-nyckel
   - OpenAI API-nyckel
3. Fältet "Sökväg till bot-kod" bör redan vara ifyllt
4. Klicka på "Spara inställningar"
5. Klicka på "Starta bot"

## Steg 3: Använd boten i Discord

När boten är igång kan du använda följande kommandon i din Discord-server:

- **Tärningskast:** `!roll 1t100` (kasta en 100-sidig tärning)
- **Expertslag:** `!ex 15 1t100` (expertslag mot färdighetsvärde 15)
- **Stridssimulering:** `!hugg`, `!stick`, `!kross`, `!fummel`
- **Kunskapssökning:** `!ask [fråga]`, `!sök [nyckelord]`, `!allt [detaljerad sökning]`
- **Regler:** `!regel [regelterm]`
- **Statistik:** `!stats`, `!mystats`
- **Sessionshantering:** `!startsession`, `!endsession`

## Felsökning

Om du stöter på problem:

- **Boten startar inte:** Kontrollera att alla API-nycklar är korrekt inmatade och att bot-sökvägen är korrekt.
- **Boten ansluter inte till Discord:** Kontrollera din internetanslutning och att Discord Token är korrekt.
- **Kommandon fungerar inte:** Kontrollera att boten har rätt behörigheter i Discord-servern.
- **Felmeddelanden i loggfliken:** Notera felmeddelandet och kontakta personen som gav dig programmet för hjälp.

## Kontakt och support

Om du behöver hjälp, kontakta personen som gav dig denna applikation.