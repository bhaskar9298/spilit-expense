# tests/test_phase3_splits.py
"""Phase 3 Tests: Split Calculations"""

import pytest
from decimal import Decimal
from server.utils.splits import (
    calculate_equal_split,
    calculate_exact_split,
    calculate_percentage_split,
    calculate_splits
)

# ============================================================================
# TEST: Equal Split
# ============================================================================

def test_equal_split_basic():
    """Test basic equal split"""
    participants = ["user1", "user2", "user3"]
    splits = calculate_equal_split(100.00, participants)
    
    total = sum(splits.values())
    assert float(total) == 100.00
    assert len(splits) == 3
    print("✓ Equal split basic works")

def test_equal_split_rounding():
    """Test equal split handles rounding correctly"""
    participants = ["user1", "user2", "user3"]
    splits = calculate_equal_split(10.00, participants)
    
    # Should be: 3.34, 3.33, 3.33
    total = sum(splits.values())
    assert float(total) == 10.00
    print("✓ Equal split rounding works")

# ============================================================================
# TEST: Exact Split
# ============================================================================

def test_exact_split_valid():
    """Test exact split with valid amounts"""
    user_amounts = {
        "user1": 60.00,
        "user2": 25.00,
        "user3": 15.00
    }
    splits = calculate_exact_split(100.00, user_amounts)
    
    assert float(splits["user1"]) == 60.00
    assert float(splits["user2"]) == 25.00
    assert float(splits["user3"]) == 15.00
    print("✓ Exact split valid works")

def test_exact_split_invalid_total():
    """Test exact split fails when amounts don't match"""
    user_amounts = {
        "user1": 60.00,
        "user2": 30.00  # Only 90, not 100
    }
    
    with pytest.raises(ValueError):
        calculate_exact_split(100.00, user_amounts)
    print("✓ Exact split validation works")

# ============================================================================
# TEST: Percentage Split
# ============================================================================

def test_percentage_split_valid():
    """Test percentage split with valid percentages"""
    user_percentages = {
        "user1": 50.0,
        "user2": 30.0,
        "user3": 20.0
    }
    splits = calculate_percentage_split(100.00, user_percentages)
    
    assert float(splits["user1"]) == 50.00
    assert float(splits["user2"]) == 30.00
    assert float(splits["user3"]) == 20.00
    print("✓ Percentage split valid works")

def test_percentage_split_invalid_total():
    """Test percentage split fails when not 100%"""
    user_percentages = {
        "user1": 50.0,
        "user2": 30.0  # Only 80%, not 100%
    }
    
    with pytest.raises(ValueError):
        calculate_percentage_split(100.00, user_percentages)
    print("✓ Percentage split validation works")

# ============================================================================
# TEST: Main calculate_splits Function
# ============================================================================

def test_calculate_splits_equal():
    """Test calculate_splits with equal type"""
    participants = ["user1", "user2"]
    splits = calculate_splits(
        total_amount=50.00,
        split_type="equal",
        participants=participants,
        paid_by="user1"
    )
    
    assert len(splits) == 2
    assert float(sum(splits.values())) == 50.00
    print("✓ calculate_splits equal works")

def test_calculate_splits_exact():
    """Test calculate_splits with exact type"""
    participants = ["user1", "user2"]
    splits = calculate_splits(
        total_amount=50.00,
        split_type="exact",
        participants=participants,
        paid_by="user1",
        split_data={"user_amounts": {"user1": 30.00, "user2": 20.00}}
    )
    
    assert float(splits["user1"]) == 30.00
    assert float(splits["user2"]) == 20.00
    print("✓ calculate_splits exact works")

def test_calculate_splits_percentage():
    """Test calculate_splits with percentage type"""
    participants = ["user1", "user2"]
    splits = calculate_splits(
        total_amount=100.00,
        split_type="percentage",
        participants=participants,
        paid_by="user1",
        split_data={"user_percentages": {"user1": 60.0, "user2": 40.0}}
    )
    
    assert float(splits["user1"]) == 60.00
    assert float(splits["user2"]) == 40.00
    print("✓ calculate_splits percentage works")

# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("PHASE 3 SPLIT CALCULATION TESTS")
    print("="*70)
    
    # Equal split tests
    test_equal_split_basic()
    test_equal_split_rounding()
    
    # Exact split tests
    test_exact_split_valid()
    test_exact_split_invalid_total()
    
    # Percentage split tests
    test_percentage_split_valid()
    test_percentage_split_invalid_total()
    
    # Main function tests
    test_calculate_splits_equal()
    test_calculate_splits_exact()
    test_calculate_splits_percentage()
    
    print("\n" + "="*70)
    print("✓ ALL PHASE 3 TESTS PASSED")
    print("="*70)
