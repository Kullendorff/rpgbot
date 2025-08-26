"""
Homeland Selection Step for Character Creation

This module handles the homeland selection step where the player chooses
their character's homeland, which will influence available races in the next step.
"""

import discord
from discord.ext import commands
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path

from .base_step import BaseStep


class HomelandStep(BaseStep):
    """Step 2: Homeland selection for the character."""
    
    def __init__(self, embed_factory, data_dir: Optional[Path] = None):
        """
        Initialize the homeland selection step.
        
        Args:
            embed_factory: The embed factory for creating Discord embeds
            data_dir: Optional data directory path
        """
        super().__init__(step_name="hemland", step_number=2)
        self.embed_factory = embed_factory
        self.data_dir = data_dir or self._get_default_data_dir()
        self.homelands: List[Dict[str, str]] = []
        self._load_homelands()
    
    def _get_default_data_dir(self) -> Path:
        """Get default data directory."""
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent
        return project_root / 'data' / 'character_tables'
    
    def _load_homelands(self) -> None:
        """Load homeland data from text files."""
        homeland_dir = self.data_dir / 'landerhemort'
        
        if not homeland_dir.exists():
            print(f"Warning: Could not find {homeland_dir}")
            return
        
        homelands = []
        
        for txt_file in sorted(homeland_dir.glob("*.txt")):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                homeland_name = txt_file.stem
                
                # Extract first line as title
                lines = content.split('\n')
                title = lines[0] if lines else homeland_name
                
                homelands.append({
                    'name': homeland_name,
                    'title': title,
                    'description': content,
                    'file_path': str(txt_file)
                })
                
            except Exception as e:
                print(f"Error loading {txt_file}: {e}")
        
        self.homelands = homelands
        print(f"Loaded {len(homelands)} homelands")
    
    async def execute(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """
        Execute the homeland selection step.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            
        Returns:
            Discord embed displaying the homeland selection
        """
        embed = self.embed_factory.admin_message(
            session.user_id,
            f"🏰 Steg {self.step_number}/{session.max_steps}: Hemland",
            "Välj rollpersonens hemland:"
        )
        
        if not self.homelands:
            embed.add_field(
                name="❌ Fel",
                value="Inga hemländer kunde laddas från systemet.",
                inline=False
            )
            await ctx.send(embed=embed)
            return embed
        
        # Split homelands into chunks for better display
        chunk_size = 15
        homeland_chunks = [self.homelands[i:i + chunk_size] 
                          for i in range(0, len(self.homelands), chunk_size)]
        
        for i, chunk in enumerate(homeland_chunks):
            chunk_title = f"Hemländer ({i*chunk_size + 1}-{i*chunk_size + len(chunk)})"
            
            homeland_list = []
            for j, homeland in enumerate(chunk):
                homeland_number = i * chunk_size + j + 1
                homeland_list.append(f"{homeland_number}. {homeland['title']}")
            
            embed.add_field(
                name=chunk_title,
                value="\n".join(homeland_list),
                inline=True
            )
        
        embed.add_field(
            name="📝 Instruktioner",
            value=(
                "Skriv hemlandets namn eller nummer\n"
                "För mer info: `info [nummer]`\n"
                "För slumpmässigt val: `slumpa`"
            ),
            inline=False
        )
        
        embed.set_footer(text="Exempel: !chargen Soldarn, !chargen 5, eller !chargen info 12")
        
        await ctx.send(embed=embed)
        return embed
    
    async def handle_input(self, ctx: commands.Context, session: 'CharacterSession', 
                          input_text: str, *args) -> Tuple[bool, Optional[str]]:
        """
        Handle user input for homeland selection.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            input_text: User's input text
            *args: Additional arguments (unused)
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        input_text = input_text.strip()
        
        # Handle info request
        if input_text.lower().startswith('info'):
            await self._handle_info_request(ctx, input_text)
            return False, "Info request handled"
        
        # Handle random selection
        if input_text.lower() in ['slumpa', 'random', 'rand']:
            return await self._handle_random_selection(ctx, session)
        
        # Handle homeland selection
        selected_homeland = self._validate_homeland_choice(input_text)
        
        if not selected_homeland:
            available_names = [h['title'] for h in self.homelands[:10]]  # Show first 10
            error_msg = (
                f"❌ Ogiltigt hemland: '{input_text}'\n\n"
                f"**Exempel på giltiga hemländer:**\n" + 
                "\n".join(f"• {name}" for name in available_names) +
                f"\n\n*Skriv `!chargen [hemlandsnamn]` eller använd nummer*"
            )
            await ctx.send(error_msg)
            return False, "Invalid homeland choice"
        
        # Store selected homeland
        session.data['hemland'] = selected_homeland['name']
        session.data['hemland_title'] = selected_homeland['title']
        
        # Send confirmation
        confirmation_embed = discord.Embed(
            title="✅ Hemland bekräftat",
            description=f"**{selected_homeland['title']}** har valts som hemland.",
            color=discord.Color.green()
        )
        
        # Add preview of homeland description (first few lines)
        description_lines = selected_homeland['description'].split('\n')
        preview = '\n'.join(description_lines[:3])
        if len(description_lines) > 3:
            preview += "\n*...*"
        
        confirmation_embed.add_field(
            name="📜 Beskrivning",
            value=preview[:500],  # Discord field limit
            inline=False
        )
        
        await ctx.send(embed=confirmation_embed)
        
        return True, None
    
    async def _handle_info_request(self, ctx: commands.Context, input_text: str) -> None:
        """Handle info request for a specific homeland."""
        parts = input_text.split()
        if len(parts) < 2:
            await ctx.send("❌ Ange vilket hemland du vill ha info om. Exempel: `info 5`")
            return
        
        try:
            homeland_number = int(parts[1])
            if 1 <= homeland_number <= len(self.homelands):
                homeland = self.homelands[homeland_number - 1]
                
                info_embed = discord.Embed(
                    title=f"📍 {homeland['title']}",
                    description=homeland['description'][:4000],  # Discord description limit
                    color=discord.Color.blue()
                )
                
                info_embed.set_footer(text=f"Hemland #{homeland_number}")
                await ctx.send(embed=info_embed)
            else:
                await ctx.send(f"❌ Ogiltigt nummer. Välj mellan 1 och {len(self.homelands)}.")
                
        except ValueError:
            await ctx.send("❌ Använd ett giltigt nummer. Exempel: `info 5`")
    
    async def _handle_random_selection(self, ctx: commands.Context, 
                                     session: 'CharacterSession') -> Tuple[bool, Optional[str]]:
        """Handle random homeland selection."""
        if not self.homelands:
            await ctx.send("❌ Inga hemländer tillgängliga för slumpval.")
            return False, "No homelands available"
        
        import random
        selected_homeland = random.choice(self.homelands)
        
        # Store the selection
        session.data['hemland'] = selected_homeland['name']
        session.data['hemland_title'] = selected_homeland['title']
        
        # Send result
        random_embed = discord.Embed(
            title="🎲 Slumpmässigt hemland",
            description=f"**{selected_homeland['title']}** har slumpats fram!",
            color=discord.Color.gold()
        )
        
        # Add preview
        description_lines = selected_homeland['description'].split('\n')
        preview = '\n'.join(description_lines[:2])
        if len(description_lines) > 2:
            preview += "\n*...*"
        
        random_embed.add_field(
            name="📜 Beskrivning",
            value=preview[:500],
            inline=False
        )
        
        await ctx.send(embed=random_embed)
        
        return True, None
    
    def _validate_homeland_choice(self, input_text: str) -> Optional[Dict[str, str]]:
        """
        Validate and find a homeland choice.
        
        Args:
            input_text: User's input
            
        Returns:
            Homeland dictionary if found, None otherwise
        """
        if not self.homelands:
            return None
        
        # Try as number first
        try:
            homeland_number = int(input_text.strip()) - 1  # Convert to 0-based
            if 0 <= homeland_number < len(self.homelands):
                return self.homelands[homeland_number]
        except ValueError:
            pass
        
        # Try exact name match (case insensitive)
        input_lower = input_text.lower().strip()
        for homeland in self.homelands:
            if (homeland['name'].lower() == input_lower or 
                homeland['title'].lower() == input_lower):
                return homeland
        
        # Try partial name matching
        matches = []
        for homeland in self.homelands:
            if (input_lower in homeland['name'].lower() or 
                input_lower in homeland['title'].lower()):
                matches.append(homeland)
        
        # Return exact match if only one found
        if len(matches) == 1:
            return matches[0]
        
        return None
    
    def validate_prerequisites(self, session: 'CharacterSession') -> Tuple[bool, Optional[str]]:
        """
        Validate that prerequisites for this step are met.
        
        Args:
            session: Current character creation session
            
        Returns:
            Tuple of (valid: bool, error_message: Optional[str])
        """
        # Homeland step typically comes after gender
        if 'kön' not in session.data:
            return False, "Gender must be selected before homeland"
        
        return True, None
    
    def get_summary(self, session: 'CharacterSession') -> str:
        """
        Get a summary of the selected homeland.
        
        Args:
            session: Current character creation session
            
        Returns:
            Summary string
        """
        hemland = session.data.get('hemland', 'Ej valt')
        hemland_title = session.data.get('hemland_title', hemland)
        return f"**Hemland:** {hemland_title}"
    
    def validate_data(self, session: 'CharacterSession') -> bool:
        """
        Validate that homeland data exists and is valid.
        
        Args:
            session: Current character creation session
            
        Returns:
            True if data is valid, False otherwise
        """
        if 'hemland' not in session.data:
            return False
        
        hemland = session.data['hemland']
        
        # Check if homeland exists in our loaded data
        homeland_names = [h['name'] for h in self.homelands]
        return hemland in homeland_names
    
    def can_skip(self, session: 'CharacterSession') -> bool:
        """
        Check if this step can be skipped.
        
        Homeland selection cannot be skipped as it affects race selection.
        
        Args:
            session: Current character creation session
            
        Returns:
            Always False - homeland must be selected
        """
        return False
    
    def get_help_text(self) -> str:
        """
        Get detailed help text for this step.
        
        Returns:
            Help text string
        """
        return (
            f"**Steg {self.step_number}: Hemland**\n\n"
            "Välj vilket land eller region din rollperson kommer från. "
            "Hemlandet påverkar vilka folkslag som är vanliga och tillgängliga "
            "i nästa steg.\n\n"
            "**Kommandon:**\n"
            "• **[namn/nummer]** - Välj specifikt hemland\n"
            "• **info [nummer]** - Visa detaljerad information om hemland\n"
            "• **slumpa** - Slumpmässigt val av hemland\n\n"
            "**Tips:** Använd `info` för att läsa mer om ett hemland innan du väljer."
        )
    
    def get_homeland_count(self) -> int:
        """Get total number of available homelands."""
        return len(self.homelands)
    
    def reload_homelands(self) -> bool:
        """
        Reload homeland data from files.
        
        Returns:
            True if reload successful, False otherwise
        """
        try:
            self._load_homelands()
            return len(self.homelands) > 0
        except Exception as e:
            print(f"Error reloading homelands: {e}")
            return False