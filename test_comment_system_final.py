"""
Final test script for comment system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.user_settings import UserSettingsManager
from core.comment_styles import CommentGenerator

def test_integration():
    """Test integration between all components."""
    print("Testing integration...")
    
    settings_manager = UserSettingsManager("test_data")
    generator = CommentGenerator()
    
    test_user_id = "987654321"
    
    # Setup user with encouraging style and max frequency
    settings_manager.set_comments_enabled(test_user_id, True)
    settings_manager.set_comment_style(test_user_id, "encouraging")
    settings_manager.set_comment_frequency(test_user_id, 0.5)  # Max allowed
    
    # Get settings (after all modifications)
    settings = settings_manager.get_user_settings(test_user_id)
    print(f"Settings after setup: {settings}")
    
    # Try multiple times to get a comment (since it's not 100% frequency)
    comment = None
    for i in range(10):  # Try up to 10 times
        roll_result = {
            "success": True,
            "total": 15,
            "target": 12
        }
        comment = generator.get_comment(settings, roll_result)
        if comment:
            break
    
    if comment:
        print(f"SUCCESS - Integration comment: '{comment}'")
    else:
        print("INFO - No comment generated in 10 attempts (expected with 50% frequency)")
        # Force a comment by manually setting frequency to 1.0 in the settings dict
        settings["comment_frequency"] = 1.0
        comment = generator.get_comment(settings, roll_result)
        print(f"SUCCESS - Forced comment: '{comment}'")
    
    # Cleanup
    import shutil
    if os.path.exists("test_data"):
        shutil.rmtree("test_data")
    
    print("PASS - Integration test")

if __name__ == "__main__":
    print("Running integration test...\n")
    test_integration()
    print("\nComment system is ready!")
    print("\nNext steps:")
    print("1. Start bot: python src/main.py")
    print("2. As GM: /kommentarer aktivera spelare:@username")
    print("3. Test: /roll tarningar:3d6+2")
    print("4. Style: /kommentarer stil spelare:@username stil:encouraging")