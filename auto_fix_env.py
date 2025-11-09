#!/usr/bin/env python3
"""
Automatic .env file fixer - makes the required changes automatically.
"""
import os
import shutil
from datetime import datetime

def auto_fix_env():
    """Automatically fix the .env file with correct values."""
    print("🔧 AUTOMATIC .env FILE FIXER")
    print("=" * 40)
    
    env_file = ".env"
    
    if not os.path.exists(env_file):
        print("❌ .env file not found!")
        print("   Make sure you're in the project directory")
        return False
    
    # Create backup
    backup_file = f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(env_file, backup_file)
    print(f"📋 Created backup: {backup_file}")
    
    try:
        # Read current file
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Track changes
        changes_made = []
        
        # Process each line
        for i, line in enumerate(lines):
            original_line = line.strip()
            
            # Fix USE_MOCKS
            if line.startswith('USE_MOCKS=true'):
                lines[i] = 'USE_MOCKS=false\n'
                changes_made.append(f"Line {i+1}: USE_MOCKS=true → USE_MOCKS=false")
            
            # Fix model name
            elif line.startswith('LLM_MODEL=nvidia/nvidia-nemotron'):
                lines[i] = 'LLM_MODEL=nvidia/NVIDIA-Nemotron-Nano-9B-v2\n'
                changes_made.append(f"Line {i+1}: Fixed model name format")
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        # Report results
        if changes_made:
            print("✅ Changes made:")
            for change in changes_made:
                print(f"   {change}")
            
            print()
            print("🎉 .env file has been automatically fixed!")
            print()
            print("🧪 Test your fixes:")
            print("   python verify_fix.py")
            print()
            print("🚀 Run your app:")
            print("   streamlit run app.py")
            
            return True
        else:
            print("ℹ️  No changes needed - file already looks correct")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing file: {e}")
        print(f"💡 Restoring backup: {backup_file}")
        shutil.copy2(backup_file, env_file)
        return False

if __name__ == "__main__":
    success = auto_fix_env()
    
    if success:
        print()
        print("✅ Done! Your .env file should now work with live API mode.")
    else:
        print()
        print("❌ Auto-fix failed. Please edit the file manually.")
        print("   Look for these lines and change them:")
        print("   USE_MOCKS=true → USE_MOCKS=false")
        print("   LLM_MODEL=nvidia/nvidia-... → LLM_MODEL=nvidia/NVIDIA-Nemotron-Nano-9B-v2")
