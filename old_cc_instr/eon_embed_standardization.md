# EON Discord Bot - Enhetlig Embed Standardisering

## UPPDRAG ÖVERSIKT
**MÅL:** Alla Discord embeds i EON-boten ska ha identisk visuell profil - samma typsnitt, spacing, emojis, och strukturlayout oavsett vilket kommando som används.

**OMFATTNING:** Detta är en stor refaktorering som kommer påverka ALLA kommando-moduler. Varje fil som skapar Discord embeds måste modifieras.

**KRITISK FRAMGÅNGSFAKTOR:** Alla `discord.Embed()` anrop måste ersättas med standardiserade factory methods. Ingen embed får skapas utanför factory-klassen.

---

## STEG 1: Skapa Embed Factory (HÖGSTA PRIORITET)

### 1.1 OBLIGATORISK: Skapa `src/core/embed_factory.py`

**VIKTIGT:** Denna fil är hjärtat i hela standardiseringen. Den MÅSTE skapas först innan någon annan ändring görs.

**PLACERING:** Exakt sökväg `src/core/embed_factory.py` (skapa `core/` mappen om den inte finns)

**KRAV:** Denna klass ska vara den ENDA källan för embed-skapande i hela projektet.

```python
"""
Centraliserad embed factory för konsekvent visuell profil.
Alla Discord embeds i boten ska skapas genom denna factory.
"""

import discord
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

class EmbedFactory:
    """Factory-klass för att skapa standardiserade Discord embeds."""
    
    # Standardfärger
    SUCCESS_COLOR = 0x2ECC71    # Grön
    ERROR_COLOR = 0xE74C3C      # Röd  
    WARNING_COLOR = 0xF39C12    # Orange
    INFO_COLOR = 0x3498DB       # Blå
    
    # Standard emojis
    DICE_EMOJI = "🎲"
    SUCCESS_EMOJI = "✅"
    FAILURE_EMOJI = "❌"
    COMBAT_EMOJI = "⚔️"
    STATS_EMOJI = "📊"
    KNOWLEDGE_EMOJI = "📚"
    ADMIN_EMOJI = "🔧"
    
    def __init__(self, color_handler):
        """Initialisera med color_handler för användarfärger."""
        self.color_handler = color_handler
    
    def _get_base_embed(self, user_id: int, title: str, description: str = None) -> discord.Embed:
        """Skapa bas-embed med användarfärg och standardformatering."""
        color = self.color_handler.get_user_color(user_id)
        embed = discord.Embed(title=title, description=description, color=color)
        embed.timestamp = datetime.utcnow()
        return embed
    
    def dice_result(self, user_id: int, user_name: str, command: str, 
                   dice_expr: str, results: List[int], total: int = None,
                   target: int = None, success: bool = None) -> discord.Embed:
        """Standard mall för tärningsresultat."""
        title = f"{self.DICE_EMOJI} Tärningskast"
        
        # Bygg description
        desc_parts = [f"**{user_name}** rullade `{dice_expr}`"]
        if command != "roll":
            desc_parts.append(f"*(kommando: {command})*")
            
        embed = self._get_base_embed(user_id, title, "\n".join(desc_parts))
        
        # Resultat field
        result_text = f"**Tärningar:** {results}"
        if total is not None:
            result_text += f"\n**Summa:** {total}"
        if target is not None:
            result_text += f"\n**Målvärde:** {target}"
            
        embed.add_field(name="Resultat", value=result_text, inline=False)
        
        # Success/failure indikation
        if success is not None:
            status_emoji = self.SUCCESS_EMOJI if success else self.FAILURE_EMOJI
            status_text = "Lyckat!" if success else "Misslyckat"
            embed.add_field(name="Utfall", value=f"{status_emoji} {status_text}", inline=True)
            
        return embed
    
    def combat_result(self, user_id: int, user_name: str, weapon: str,
                     attack_roll: int, damage_rolls: List[int], 
                     hit_zone: str = None, special_effects: List[str] = None) -> discord.Embed:
        """Standard mall för stridsresultat."""
        title = f"{self.COMBAT_EMOJI} Attackresultat"
        description = f"**{user_name}** attackerar med {weapon}"
        
        embed = self._get_base_embed(user_id, title, description)
        
        # Attack field
        embed.add_field(name="Attackslag", value=f"**{attack_roll}**", inline=True)
        
        # Damage field
        if damage_rolls:
            damage_text = f"**Skada:** {damage_rolls}\n**Total:** {sum(damage_rolls)}"
            embed.add_field(name="Skada", value=damage_text, inline=True)
        
        # Hit zone
        if hit_zone:
            embed.add_field(name="Träffzon", value=hit_zone, inline=True)
            
        # Special effects
        if special_effects:
            effects_text = "\n".join(f"• {effect}" for effect in special_effects)
            embed.add_field(name="Specialeffekter", value=effects_text, inline=False)
            
        return embed
    
    def stats_overview(self, user_id: int, user_name: str, stats_data: Dict[str, Any],
                      session_id: str = None) -> discord.Embed:
        """Standard mall för statistiköversikt."""
        title = f"{self.STATS_EMOJI} Statistik"
        description = f"Översikt för **{user_name}**"
        if session_id:
            description += f"\n*Session: {session_id}*"
            
        embed = self._get_base_embed(user_id, title, description)
        
        # Grundläggande stats
        basic_stats = [
            f"**Totala kast:** {stats_data.get('total_rolls', 0)}",
            f"**Lyckade kast:** {stats_data.get('successes', 0)}",
            f"**Misslyckade kast:** {stats_data.get('failures', 0)}"
        ]
        
        if stats_data.get('success_rate') is not None:
            basic_stats.append(f"**Träffsäkerhet:** {stats_data['success_rate']:.1f}%")
            
        embed.add_field(name="Grundstatistik", value="\n".join(basic_stats), inline=False)
        
        return embed
    
    def knowledge_result(self, user_id: int, user_name: str, question: str,
                        answer: str, sources: List[str] = None) -> discord.Embed:
        """Standard mall för kunskapsresultat."""
        title = f"{self.KNOWLEDGE_EMOJI} Kunskapssökning"
        description = f"**Fråga från {user_name}:**\n*{question}*"
        
        embed = self._get_base_embed(user_id, title, description)
        
        # Svar (med längdbegränsning)
        answer_text = answer[:1000] + "..." if len(answer) > 1000 else answer
        embed.add_field(name="Svar", value=answer_text, inline=False)
        
        # Källor om tillgängliga
        if sources:
            sources_text = "\n".join(f"• {source}" for source in sources[:3])
            if len(sources) > 3:
                sources_text += f"\n*...och {len(sources) - 3} till*"
            embed.add_field(name="Källor", value=sources_text, inline=False)
            
        return embed
    
    def error_message(self, user_id: int, error_msg: str, 
                     suggestion: str = None) -> discord.Embed:
        """Standard mall för felmeddelanden."""
        embed = discord.Embed(
            title="❌ Fel",
            description=error_msg,
            color=self.ERROR_COLOR
        )
        embed.timestamp = datetime.utcnow()
        
        if suggestion:
            embed.add_field(name="Förslag", value=suggestion, inline=False)
            
        return embed
    
    def success_message(self, user_id: int, message: str) -> discord.Embed:
        """Standard mall för framgångsmeddelanden."""
        embed = discord.Embed(
            title="✅ Klart",
            description=message,
            color=self.SUCCESS_COLOR
        )
        embed.timestamp = datetime.utcnow()
        return embed
    
    def admin_message(self, user_id: int, title: str, content: str) -> discord.Embed:
        """Standard mall för admin-meddelanden."""
        embed_title = f"{self.ADMIN_EMOJI} {title}"
        embed = self._get_base_embed(user_id, embed_title, content)
        return embed
```

## STEG 2: KARTLÄGG BEFINTLIGA EMBEDS (KRITISKT FÖR PLANERING)

**VARFÖR DETTA STEG ÄR VIKTIGT:** Utan fullständig kartläggning riskerar vi att missa embeds, vilket leder till inkonsistent resultat.

### 2.1 OBLIGATORISK: Kör fullständig audit

**EXAKT KOMMANDO ATT KÖRA:**
```bash
# Från projektets root-katalog (C:\Diceroller\)
# Hitta alla Python-filer som skapar embeds
find src/ -name "*.py" -exec grep -l "discord\.Embed\|embed\s*=" {} \; > embed_files.txt

# Detaljerad analys av embed-patterns (SPARA OUTPUT)
grep -r "discord\.Embed\|\.add_field\|embed\s*=" src/ --include="*.py" -n > embed_patterns.txt

# Hitta alla färganvändningar
grep -r "color\s*=" src/ --include="*.py" -n > color_usage.txt
```

**RESULTAT KRÄVS:** Tre textfiler med alla embed-användningar innan du fortsätter.

### 2.2 OBLIGATORISK: Dokumentera alla embed-kategorier

**SKAPA INVENTERING AV:**
1. **Tärningsresultat embeds** - Hitta i `dice_commands.py` och relaterade filer
2. **Strids embeds** - Hitta i `combat_commands.py` 
3. **Statistik embeds** - Hitta i `stats_commands.py`
4. **Kunskaps embeds** - Hitta i `knowledge_commands.py`
5. **Admin embeds** - Hitta i `admin_commands.py`
6. **Error embeds** - Spridda överallt, hitta alla!

**KRITISK FRÅGA:** Vilka typer av embeds finns och hur ser de ut nu? Detta avgör vilka factory methods som behövs.

## STEG 3: SYSTEMATISK REPLACEMENT (FARLIG ZON - KRÄVER PRECISION)

**VARNING:** Detta steg kan krasha boten om det görs fel. Gör EN modul i taget och testa efter varje ändring.

**OBLIGATORISK ORDNING:** Uppdatera moduler i denna exakta ordning för att minimera risk:

### 3.1 FÖRST: Uppdatera main.py (KRITISKT)

**EXAKT ÄNDRING I `src/main.py`:**

**HITTA DENNA SEKTION:**
```python
# Där color_handler initialiseras
color_handler = ColorHandler()
```

**LÄGG TILL DIREKT EFTER:**
```python
# Skapa embed factory (MÅSTE komma efter color_handler)
from core.embed_factory import EmbedFactory
embed_factory = EmbedFactory(color_handler)
```

**HITTA ALLA register_*_commands() ANROP OCH LÄGG TILL embed_factory:**
```python
# INNAN (hitta dessa rader)
register_dice_commands(bot, roll_tracker, color_handler)
register_combat_commands(bot, combat_manager, color_handler)
register_stats_commands(bot, roll_tracker, color_handler)
register_knowledge_commands(bot, knowledge_base, color_handler)
register_admin_commands(bot, roll_tracker, color_handler, knowledge_base)

# EFTER (ersätt med dessa)
register_dice_commands(bot, roll_tracker, color_handler, embed_factory)
register_combat_commands(bot, combat_manager, color_handler, embed_factory)
register_stats_commands(bot, roll_tracker, color_handler, embed_factory)
register_knowledge_commands(bot, knowledge_base, color_handler, embed_factory)
register_admin_commands(bot, roll_tracker, color_handler, knowledge_base, embed_factory)
```

### 3.2 ANDRA: Uppdatera register-funktioner

**I VARJE kommando-fil, HITTA register-funktionen och LÄGG TILL embed_factory parameter:**

**EXEMPEL från `src/commands/dice_commands.py`:**
```python
# INNAN
def register_dice_commands(bot, roll_tracker, color_handler):

# EFTER  
def register_dice_commands(bot, roll_tracker, color_handler, embed_factory):
```

**UPPREPA för ALLA dessa filer:**
- `src/commands/dice_commands.py`
- `src/commands/combat_commands.py`
- `src/commands/stats_commands.py`
- `src/commands/knowledge_commands.py`
- `src/commands/admin_commands.py`

### 3.3 TREDJE: Ersätt embeds EN MODUL I TAGET

**TESTNINGSKRAV:** Efter varje modul-uppdatering - starta boten och testa att kommandona fungerar!

#### 3.3.1 Starta med `dice_commands.py` (lägst risk)

**HITTA ALLA VARIANTER AV:**
```python
# Gamla patterns att ersätta
embed = discord.Embed(title="🎲 ...", color=color)
embed.add_field(name="...", value="...")
await ctx.send(embed=embed)
```

**ERSÄTT MED:**
```python
# Ny standardiserad approach
embed = embed_factory.dice_result(
    ctx.author.id, 
    ctx.author.display_name,
    "roll",  # kommando-namn
    dice_expr,  # vad som kastades
    results,  # lista med resultat
    total,  # summa (eller None)
    target,  # målvärde (eller None)  
    success  # True/False/None
)
await ctx.send(embed=embed)
```

#### 3.3.2 Fortsätt med övriga moduler

**SAMMA PROCESS för:**
- `combat_commands.py` → använd `combat_result()`
- `stats_commands.py` → använd `stats_overview()`  
- `knowledge_commands.py` → använd `knowledge_result()`
- `admin_commands.py` → använd `admin_message()` eller `success_message()`

**KRITISKT:** Testa boten efter VARJE modul-uppdatering!

## STEG 4: VALIDERING OCH TESTING (KRITISKT FÖR SÄKERHET)

**VARNING:** Utan ordentlig testning kommer boten troligen krasha eller visa trasiga embeds.

### 4.1 OBLIGATORISK: Skapa och kör test script

**SKAPA EXAKT FIL:** `test_embeds.py` i projektets root

**DETTA SCRIPT MÅSTE KÖRAS INNAN DEPLOYMENT:**

```python
# test_embeds.py
"""Test script för att verifiera embed standardisering."""

import asyncio
import discord
from unittest.mock import MagicMock
from core.embed_factory import EmbedFactory
from core.color_handler import ColorHandler

async def test_embed_consistency():
    """Testa att alla embed-typer följer samma standarder."""
    
    # Mock objects
    color_handler = ColorHandler()
    embed_factory = EmbedFactory(color_handler)
    
    test_user_id = 12345
    test_user_name = "TestUser"
    
    # Test alla embed-typer
    embeds = [
        embed_factory.dice_result(test_user_id, test_user_name, "roll", "3d6", [4,5,6], 15, 12, True),
        embed_factory.combat_result(test_user_id, test_user_name, "Svärd", 14, [6,3], "Torso"),
        embed_factory.stats_overview(test_user_id, test_user_name, {"total_rolls": 42, "successes": 28}),
        embed_factory.knowledge_result(test_user_id, test_user_name, "Vad är EON?", "EON är ett rollspel..."),
        embed_factory.error_message(test_user_id, "Ogiltigt kommando"),
        embed_factory.success_message(test_user_id, "Session startad")
    ]
    
    # Verifiera konsistens
    for embed in embeds:
        assert embed.timestamp is not None, "Alla embeds ska ha timestamp"
        assert embed.color is not None, "Alla embeds ska ha färg"
        assert len(embed.title) > 0, "Alla embeds ska ha titel"
    
    print("✅ Alla embed-tester godkända!")

if __name__ == "__main__":
    asyncio.run(test_embed_consistency())
```

### 4.2 OBLIGATORISK: Manuell testning

**TESTNING MÅSTE GÖRAS I DENNA ORDNING:**

1. **Starta boten** - Kontrollera att den startar utan fel
2. **Testa grundläggande tärningskommandon:**
   - `!roll 3d6`
   - `!ex 5` 
   - `!count 3d6 >=4`
3. **Testa stridskommandon:**
   - `!hugg`
   - `!stick`
4. **Testa statistikkommandon:**
   - `!mystats`
   - `!stats`
5. **Testa kunskapskommandon:**
   - `!ask test fråga`
6. **Testa admin-kommandon** (om du har GM-rollen):
   - `!startsession`

**KONTROLLERA FÖR VARJE KOMMANDO:**
- ✅ Embed visas korrekt
- ✅ Samma typsnitt och spacing som andra embeds
- ✅ Användarfärg fungerar
- ✅ Emojis visas rätt
- ✅ Timestamps finns på alla embeds
- ✅ Inga Python-fel i konsolen

### 4.3 OBLIGATORISK: Visuell jämförelse

**FÖRE DEPLOYMENT:**
1. Ta skärmdumpar av varje kommando-typ
2. Jämför att alla ser identiska ut (bortsett från innehåll)
3. Kontrollera att inga gamla embed-stilar kvarstår

**OM NÅGOT SER ANNORLUNDA UT:** Stoppa och fixa innan du fortsätter!

## STEG 5: SÄKERHETSVALIDERING (ABSOLUT KRITISKT)

**DETTA STEG AVGÖR OM PROJEKTET LYCKAS ELLER MISSLYCKAS**

### 5.1 Code Review Checklist (OBLIGATORISK)

**KRAV INNAN DEPLOYMENT:**
- [ ] **NOLL** `discord.Embed()` anrop utanför `embed_factory.py`
- [ ] **ALLA** kommando-moduler importerar och använder `embed_factory`  
- [ ] **ALLA** `register_*_commands()` funktioner har `embed_factory` parameter
- [ ] **ALLA** embed-skapanden använder factory methods
- [ ] **KONSEKVENT** parameter-ordning i alla factory method-anrop
- [ ] **ENHETLIG** error handling för embed-fel
- [ ] **INGA** gamla import-statements för embed-skapande kvar

### 5.2 Final Audit (OBLIGATORISK)

**KÖRS EFTER ALL REFAKTORERING:**
```bash
# DETTA KOMMANDO SKA RETURNERA 0 RESULTAT (endast embed_factory.py)
grep -r "discord\.Embed" src/ --include="*.py" | grep -v "embed_factory.py"

# OM OVANSTÅENDE HITTAR NÅGOT = REFAKTORERINGEN ÄR INTE KLAR!
```

**OM AUDIT MISSLYCKAS:** Stoppa allt och fixa de embed-skapanden som missades.

---

## POTENTIELLA FALLGROPAR (LÄS DETTA!)

### Fallgrop 1: Inkomplett replacement
**PROBLEM:** Missade embed-skapanden leder till inkonsistent utseende
**LÖSNING:** Kör audit-kommandot ovan - det får INTE hitta några `discord.Embed` utanför factory

### Fallgrop 2: Import errors  
**PROBLEM:** Factory importeras fel eller inte alls
**LÖSNING:** Kontrollera att `core/` mappen finns och att imports är korrekta

### Fallgrop 3: Parameter missmatch
**PROBLEM:** Factory methods anropas med fel parametrar
**LÖSNING:** Följ exakt de method signatures som definieras i factory-klassen

### Fallgrop 4: Color handler dependency
**PROBLEM:** Embed factory initialiseras innan color_handler
**LÖSNING:** Säkerställ ordning i main.py: först color_handler, sedan embed_factory

### Fallgrop 5: Icke-testade kommandon
**PROBLEM:** Kommandon som inte testas kan innehålla buggar
**LÖSNING:** Testa VARJE kommando-typ manuellt innan deployment

---

## SLUTLIGT ACCEPTANSKRAV

**PROJEKTET ÄR KLART NÄR:**
1. ✅ Alla embeds skapas via `EmbedFactory` 
2. ✅ Visuell konsistens verifierad genom skärmdumpar
3. ✅ Alla kommandon fungerar utan fel
4. ✅ Code audit visar 0 `discord.Embed` utanför factory
5. ✅ Manuell testning av alla kommando-typer genomförd

**OM NÅGOT AV OVANSTÅENDE SAKNAS = PROJEKTET ÄR INTE KLART**