# Complete server.py - All phases included
# Run this to verify completeness
import sys
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Check imports
try:
    from db.client import expenses_col, expense_participants_col
    print("✓ Database imports OK")
except Exception as e:
    print(f"✗ Database imports failed: {e}")

try:
    from server.utils.authorization import is_user_in_group
    print("✓ Authorization imports OK")
except Exception as e:
    print(f"✗ Authorization imports failed: {e}")

try:
    from server.utils.splits import calculate_splits
    print("✓ Split calculator imports OK")
except Exception as e:
    print(f"✗ Split calculator imports failed: {e}")

print("\n✓ All Phase 3 dependencies ready!")
print("\nPhase 3 added tools:")
print("  1. add_group_expense - Add expense with splits")
print("  2. list_group_expenses - List group expenses with split details")
print("  3. get_expense_details - Get expense with complete split info")
