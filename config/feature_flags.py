"""
Feature flags för gradvis aktivering av slash commands.
Möjliggör säker migration och dual mode (både prefix och slash).
"""

# Feature flags för olika command-grupper
FEATURE_FLAGS = {
    # Dice commands
    "slash_dice_enabled": True,          # /roll, /ex, /count, /chance
    "dual_mode_dice": True,              # Kör både ! och / för dice commands
    
    # Combat commands  
    "slash_combat_enabled": True,        # /hugg, /stick, /kross, /fummel
    "dual_mode_combat": True,            # Kör både ! och / för combat commands
    
    # Knowledge commands
    "slash_knowledge_enabled": True,     # /ask, /sök, /allt
    "dual_mode_knowledge": True,         # Kör både ! och / för knowledge commands
    
    # Admin commands
    "slash_admin_enabled": False,        # /startsession, /endsession etc
    "dual_mode_admin": False,            # Kör både ! och / för admin commands
    
    # Utility commands
    "slash_utility_enabled": True,       # /stats, /mystats, /regel etc
    "dual_mode_utility": True,           # Kör både ! och / för utility commands
    
    # Character creation
    "slash_chargen_enabled": False,      # /chargen
    "dual_mode_chargen": False,          # Kör både ! och / för chargen
    
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
    
    # Knowledge commands - aktivera för test
    "ask": True,
    "sök": True,
    "allt": True,
    
    # Admin commands - alla av för nu
    "startsession": False,
    "endsession": False,
    "showsession": False,
    "secret": False,
    
    # Utility commands - aktivera för test
    "stats": True,
    "mystats": True,
    "regel": True,
    "höj": True,
    "help": True,
    
    # Character creation - av för nu
    "chargen": False,
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

def is_dual_mode_enabled(group: str) -> bool:
    """
    Kontrollera om dual mode är aktiverat för en grupp.
    
    Args:
        group: Gruppen att kontrollera (t.ex. "dice")
        
    Returns:
        True om både prefix och slash ska köras
    """
    dual_flag = f"dual_mode_{group}"
    return FEATURE_FLAGS.get(dual_flag, False)

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

def get_migration_status() -> dict:
    """Returnera översikt över migration status."""
    return {
        "dice_commands": {
            "slash_enabled": FEATURE_FLAGS["slash_dice_enabled"],
            "dual_mode": FEATURE_FLAGS["dual_mode_dice"],
            "individual_commands": {cmd: enabled for cmd, enabled in COMMAND_FLAGS.items() 
                                  if cmd in ["roll", "ex", "count", "chance"]}
        },
        "total_slash_commands": len(get_enabled_slash_commands()),
        "migration_phase": "Phase 1 - Dice Commands" if FEATURE_FLAGS["slash_dice_enabled"] else "Preparation"
    }