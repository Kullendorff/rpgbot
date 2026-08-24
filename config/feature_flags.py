"""
Feature flags för gradvis aktivering av slash commands.
(Dual mode-prefixflaggorna är borttagna — legacy-prefixlagret raderades 2026-08-23.)
"""

# Feature flags för olika command-grupper
FEATURE_FLAGS = {
    # Dice commands
    "slash_dice_enabled": True,          # /roll, /ex, /count, /chance

    # Combat commands
    "slash_combat_enabled": True,        # /hugg, /stick, /kross, /fummel

    # Admin commands
    "slash_admin_enabled": True,         # /startsession, /endsession etc

    # Utility commands
    "slash_utility_enabled": True,       # /stats, /mystats, /regel etc
    
    # Delta Green commands
    "slash_deltagreen_enabled": True,    # /dgcheck, /dgluck, /dgstat, /dglethality, /dgsan

    # Dragonbane commands (modul av Jonas, github.com/jonsal/dragonbane)
    "slash_dragonbane_enabled": True,    # /dod_slag, /dod_fv, /dod_skada, /dod_pressa, /dod_init (modul av Jonas)

    # Star Wars D6 commands (WEG40120, 2nd Ed. Revised & Expanded)
    "slash_starwars_enabled": True,      # /sw_slag, /sw_motstand, /sw_svarighet, /sw_init

    # Spindel commands (gigantspindel + småspindlar, src/spindel/). Avstängd
    # tills vidare — sätt till True för att slå på /spindel, /spindel_runda,
    # /spindelstatus, /spindelreset, /spindeldump, /spawna_småspindlar,
    # /attack_småspindel, /småspindelstatus, /reset_småspindlar.
    "slash_spindel_enabled": False,

    # Global flags
    "enable_slash_logging": True,        # Logga alla slash command användningar
    "enable_performance_monitoring": True, # Mät execution times
    "enable_error_reporting": True,      # Rapportera fel via DM till dev
}

# Per-command granular control (overrides group flags)
COMMAND_FLAGS = {
    # Dice commands - individual control
    "roll": True,      # /roll kommando aktiverat
    "ex": True,        # /ex kommando aktiverat  
    "count": True,     # /count kommando aktiverat
    "chance": True,    # /chance kommando aktiverat
    
    # Combat commands - aktivera för test
    "hugg": True,
    "stick": True,
    "kross": True,
    "fummel": True,

    # Admin commands - aktiverade för GM
    "startsession": True,
    "endsession": True,
    "showsession": True,
    "secret": True,
    
    # Utility commands - aktivera för test
    "stats": True,
    "mystats": True,
    "regel": True,
    "höj": True,
    "help": True,
    
    # Delta Green commands
    "dgcheck": True,
    "dgstat": True,
    "dgluck": True,
    "dglethality": True,
    "dgsan": True,
    "dgagent": True,
    "dgroll": True,
    "dggmroll": True,
    "dggmstatus": True,
    "dggmset": True,
    "dgstartsession": True,
    "dgendsession": True,
    "dgdmg": True,
    "dggmdmg": True,
    "dggmreset": True,
}

def is_command_enabled(command_name: str, group: str = None) -> bool:
    """
    Kontrollera om ett specifikt kommando är aktiverat.

    Args:
        command_name: Namnet på kommandot (t.ex. "roll")
        group: Gruppen kommandot tillhör (t.ex. "dice")

    Returns:
        True om kommandot är aktiverat
    """
    # Kolla först per-command flag (högsta prioritet)
    if command_name in COMMAND_FLAGS:
        return COMMAND_FLAGS[command_name]

    # Fallback till group flag
    if group:
        group_flag = f"slash_{group}_enabled"
        return FEATURE_FLAGS.get(group_flag, False)

    # Default till False för säkerhet
    return False

def get_enabled_slash_commands() -> list:
    """Returnera lista över alla aktiverade slash commands."""
    enabled = []
    
    for command, enabled_flag in COMMAND_FLAGS.items():
        if enabled_flag:
            enabled.append(command)
    
    return enabled

def toggle_command(command_name: str, enabled: bool = None) -> bool:
    """
    Toggla ett kommando på/av eller sätt explicit värde.
    
    Args:
        command_name: Namnet på kommandot
        enabled: Explicit värde, eller None för toggle
        
    Returns:
        Nya värdet efter toggle/set
    """
    if command_name not in COMMAND_FLAGS:
        raise ValueError(f"Okänt kommando: {command_name}")

    if enabled is None:
        # Toggle
        COMMAND_FLAGS[command_name] = not COMMAND_FLAGS[command_name]
    else:
        # Explicit set
        COMMAND_FLAGS[command_name] = enabled

    return COMMAND_FLAGS[command_name]