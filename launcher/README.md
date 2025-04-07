# EON Diceroller Bot Launcher

Ett enkelt program för att konfigurera och köra EON Diceroller Bot utan tekniska kunskaper.

## Kom igång

1. **Skaffa nödvändiga API-nycklar**:
   - Discord Token (från [Discord Developer Portal](https://discord.com/developers/applications))
   - Pinecone API-nyckel (från [Pinecone](https://app.pinecone.io/))
   - Anthropic Claude API-nyckel (från [Anthropic Console](https://console.anthropic.com/))
   - OpenAI API-nyckel (från [OpenAI Platform](https://platform.openai.com/))

2. **Ladda ner bot-koden**:
   - Ladda ner koden från GitHub: `https://github.com/kullendorff/rpgbot`
   - Eller använd den befintliga bot-koden om den redan finns på din dator

3. **Konfigurera boten**:
   - Fyll i alla API-nycklar i programmet
   - Ange sökvägen till bot-koden
   - Ange Discord-kanaler där boten ska vara aktiv (valfritt)

4. **Starta boten**:
   - Klicka på "Starta bot" när allt är konfigurerat
   - Övervaka bot-statusen i loggfliken

## Vanliga frågor

### Hur hittar jag mitt Discord-kanal ID?

1. Aktivera utvecklarläge i Discord:
   - Gå till Användarinställningar
   - Välj Avancerat
   - Slå på "Utvecklarläge"

2. Högerklicka på en kanal och välj "Kopiera ID"

### Vilka kommandon har boten?

EON Diceroller Bot stödjer följande kommandon:
- Tärningskast: `!roll`, `!ex`, `!count`
- Hemliga tärningskast: `!secret`
- Kunskapsbas: `!ask`, `!sök`, `!allt`
- Regler: `!regel`
- Stridssimulering: `!hugg`, `!stick`, `!kross`, `!fummel`
- Statistik: `!stats`, `!mystats`
- Sessionshantering: `!startsession`, `!endsession`

## Felsökning

Om du stöter på problem:
1. Kontrollera att alla API-nycklar är korrekt inmatade
2. Försäkra dig om att bot-sökvägen är korrekt
3. Kontrollera loggfliken för felmeddelanden
4. Försäkra dig om att bot-användaren har rätt behörigheter i Discord

## Kontakt och support

Om du behöver hjälp, kontakta din vän som gav dig denna applikation. De vet hur man hjälper dig vidare eller kan kontakta utvecklaren vid behov.