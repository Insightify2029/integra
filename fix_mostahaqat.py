# -*- coding: utf-8 -*-
"""
Fix: Add missing methods to mostahaqat_window.py
"""

import os

BASE = os.path.dirname(os.path.abspath(__file__))
MW_FILE = os.path.join(BASE, "modules", "mostahaqat", "window", "mostahaqat_window.py")

print("=" * 50)
print("  Fix: mostahaqat_window.py")
print("=" * 50)

if not os.path.exists(MW_FILE):
    print(f"  ❌ File not found: {MW_FILE}")
    input("Press Enter...")
    exit(1)

with open(MW_FILE, "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# Check if methods already exist
if "_on_employee_saved" not in content or "def _on_employee_saved" not in content:
    # Find a good place to add - before the last method or at end of class
    # We'll add before the theme/stylesheet methods or at the end
    
    new_methods = '''
    def _on_employee_saved(self, updated_data: dict):
        """بعد حفظ التعديلات - يرجع لملف الموظف."""
        self._employee_profile_screen.set_employee(updated_data)
        self._stack.setCurrentIndex(2)
        self.statusBar().showMessage(f"\\u2705 تم حفظ: {updated_data.get('name_ar', '')}")

    def _on_edit_cancelled(self):
        """إلغاء التعديل - يرجع لملف الموظف."""
        self._stack.setCurrentIndex(2)
        self.statusBar().showMessage("تم إلغاء التعديل")
'''
    
    # Strategy: find the line with the connect that's failing and add methods after class body
    # Best approach: add before the last line of the file or find a suitable spot
    
    # Try to find _deactivate_employee or _edit_employee_data and add after it
    insert_markers = [
        "def _deactivate_employee",
        "def _edit_employee_data", 
        "def _calculate_end_of_service",
        "def _calculate_overtime",
        "def _settle_leave",
    ]
    
    inserted = False
    for marker in insert_markers:
        if marker in content:
            # Find the end of this method (next def at same indent level)
            pos = content.find(marker)
            # Find next "    def " after this one
            search_start = pos + len(marker)
            next_def = content.find("\n    def ", search_start)
            
            if next_def > 0:
                # Insert before the next def
                content = content[:next_def] + new_methods + content[next_def:]
                inserted = True
                changes += 1
                print(f"  ✅ Added _on_employee_saved after {marker}")
                print(f"  ✅ Added _on_edit_cancelled")
                break
    
    if not inserted:
        # Fallback: add at the very end of the file
        content = content.rstrip() + "\n" + new_methods + "\n"
        changes += 1
        print("  ✅ Added methods at end of file")
else:
    print("  ⏭️ Methods already exist")

# Save
with open(MW_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n  Changes: {changes}")
print()

if changes > 0:
    print("  ✅ Fixed! Now run: python main.py")
else:
    print("  No changes needed")

print("=" * 50)
input("\nPress Enter to close...")
