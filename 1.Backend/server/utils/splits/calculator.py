# server/utils/splits/calculator.py
"""
Phase 3: Split Calculation Engine

Implements three split types:
1. Equal - Divide equally among all participants
2. Exact - Specific amounts for each participant
3. Percentage - Percentage-based distribution

All calculations use Decimal for precision (no float rounding errors).
"""

from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from typing import Dict, List
from bson import ObjectId

# ============================================================================
# SPLIT CALCULATION FUNCTIONS
# ============================================================================

def calculate_equal_split(total_amount: float, participants: List[str]) -> Dict[str, Decimal]:
    """
    Divide amount equally among all participants.
    Handles rounding by giving remainder to first participant (usually the payer).
    
    Args:
        total_amount: Total expense amount
        participants: List of user IDs
        
    Returns:
        Dict mapping user_id to their share amount
        
    Example:
        total_amount = 100.00, participants = ['user1', 'user2', 'user3']
        Result: {'user1': 33.34, 'user2': 33.33, 'user3': 33.33}
    """
    if not participants:
        raise ValueError("Cannot split expense with no participants")
    
    total = Decimal(str(total_amount))
    num_participants = len(participants)
    
    # Calculate base share (rounded down to 2 decimal places)
    base_share = (total / num_participants).quantize(
        Decimal('0.01'), 
        rounding=ROUND_DOWN
    )
    
    # Calculate remainder
    allocated = base_share * num_participants
    remainder = total - allocated
    
    # Build result
    splits = {}
    for i, user_id in enumerate(participants):
        if i == 0:
            # First participant gets base share + remainder
            splits[user_id] = base_share + remainder
        else:
            splits[user_id] = base_share
    
    # Verify total
    calculated_total = sum(splits.values())
    assert calculated_total == total, f"Split total {calculated_total} != expense total {total}"
    
    return splits

def calculate_exact_split(total_amount: float, user_amounts: Dict[str, float]) -> Dict[str, Decimal]:
    """
    Validate and convert exact amounts for each participant.
    
    Args:
        total_amount: Total expense amount
        user_amounts: Dict mapping user_id to their exact share
        
    Returns:
        Dict mapping user_id to their share amount (as Decimal)
        
    Raises:
        ValueError: If amounts don't sum to total
        
    Example:
        total_amount = 100.00
        user_amounts = {'user1': 60.00, 'user2': 25.00, 'user3': 15.00}
        Validates: 60 + 25 + 15 = 100 ✓
    """
    if not user_amounts:
        raise ValueError("Cannot split expense with no participants")
    
    total = Decimal(str(total_amount))
    
    # Convert to Decimal and sum
    splits = {}
    calculated_total = Decimal('0')
    
    for user_id, amount in user_amounts.items():
        if amount < 0:
            raise ValueError(f"Amount for {user_id} cannot be negative: {amount}")
        
        decimal_amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        splits[user_id] = decimal_amount
        calculated_total += decimal_amount
    
    # Verify total matches
    if calculated_total != total:
        raise ValueError(
            f"Split amounts ({float(calculated_total)}) don't match "
            f"total expense ({float(total)}). "
            f"Difference: {float(total - calculated_total)}"
        )
    
    return splits

def calculate_percentage_split(total_amount: float, user_percentages: Dict[str, float]) -> Dict[str, Decimal]:
    """
    Calculate amounts based on percentages.
    Handles rounding to ensure sum equals total exactly.
    
    Args:
        total_amount: Total expense amount
        user_percentages: Dict mapping user_id to their percentage (0-100)
        
    Returns:
        Dict mapping user_id to their share amount
        
    Raises:
        ValueError: If percentages don't sum to 100 or are invalid
        
    Example:
        total_amount = 100.00
        user_percentages = {'user1': 50.0, 'user2': 30.0, 'user3': 20.0}
        Result: {'user1': 50.00, 'user2': 30.00, 'user3': 20.00}
    """
    if not user_percentages:
        raise ValueError("Cannot split expense with no participants")
    
    total = Decimal(str(total_amount))
    
    # Validate percentages
    total_percentage = sum(user_percentages.values())
    if abs(total_percentage - 100.0) > 0.01:  # Allow small floating point errors
        raise ValueError(
            f"Percentages must sum to 100% (got {total_percentage}%)"
        )
    
    # Validate individual percentages
    for user_id, percentage in user_percentages.items():
        if percentage < 0 or percentage > 100:
            raise ValueError(f"Invalid percentage for {user_id}: {percentage}%")
    
    # Sort by percentage (descending) for better rounding distribution
    sorted_users = sorted(
        user_percentages.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    # Calculate amounts for all but last user
    splits = {}
    running_total = Decimal('0')
    
    for i, (user_id, percentage) in enumerate(sorted_users[:-1]):
        amount = (total * Decimal(str(percentage)) / Decimal('100')).quantize(
            Decimal('0.01'), 
            rounding=ROUND_HALF_UP
        )
        splits[user_id] = amount
        running_total += amount
    
    # Last user gets remainder to avoid rounding errors
    last_user_id = sorted_users[-1][0]
    splits[last_user_id] = total - running_total
    
    # Verify total
    calculated_total = sum(splits.values())
    assert calculated_total == total, f"Split total {calculated_total} != expense total {total}"
    
    return splits

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_split_participants(participants: List[str], paid_by: str) -> None:
    """
    Validate that participants list is valid.
    
    Args:
        participants: List of user IDs
        paid_by: User ID who paid
        
    Raises:
        ValueError: If validation fails
    """
    if not participants:
        raise ValueError("At least one participant is required")
    
    if len(participants) != len(set(participants)):
        raise ValueError("Duplicate participants not allowed")
    
    if paid_by not in participants:
        raise ValueError("Payer must be included in participants list")

def validate_split_data(split_type: str, participants: List[str], split_data: dict) -> None:
    """
    Validate split data based on split type.
    
    Args:
        split_type: 'equal', 'exact', or 'percentage'
        participants: List of user IDs
        split_data: Additional split data (user_amounts or user_percentages)
        
    Raises:
        ValueError: If validation fails
    """
    if split_type == "equal":
        # No additional data needed
        pass
    
    elif split_type == "exact":
        if not split_data or "user_amounts" not in split_data:
            raise ValueError("Exact split requires 'user_amounts' data")
        
        user_amounts = split_data["user_amounts"]
        
        # Verify all participants have amounts
        for participant in participants:
            if participant not in user_amounts:
                raise ValueError(f"Missing amount for participant {participant}")
        
        # Verify no extra users
        for user_id in user_amounts:
            if user_id not in participants:
                raise ValueError(f"Amount specified for non-participant {user_id}")
    
    elif split_type == "percentage":
        if not split_data or "user_percentages" not in split_data:
            raise ValueError("Percentage split requires 'user_percentages' data")
        
        user_percentages = split_data["user_percentages"]
        
        # Verify all participants have percentages
        for participant in participants:
            if participant not in user_percentages:
                raise ValueError(f"Missing percentage for participant {participant}")
        
        # Verify no extra users
        for user_id in user_percentages:
            if user_id not in participants:
                raise ValueError(f"Percentage specified for non-participant {user_id}")
    
    else:
        raise ValueError(f"Invalid split_type: {split_type}. Must be 'equal', 'exact', or 'percentage'")

# ============================================================================
# MAIN SPLIT CALCULATION FUNCTION
# ============================================================================

def calculate_splits(
    total_amount: float,
    split_type: str,
    participants: List[str],
    paid_by: str,
    split_data: dict = None
) -> Dict[str, Decimal]:
    """
    Calculate splits based on type.
    
    Args:
        total_amount: Total expense amount
        split_type: 'equal', 'exact', or 'percentage'
        participants: List of user IDs
        paid_by: User ID who paid
        split_data: Additional data (user_amounts or user_percentages)
        
    Returns:
        Dict mapping user_id to their share amount
        
    Raises:
        ValueError: If calculation fails or validation fails
    """
    # Validate inputs
    validate_split_participants(participants, paid_by)
    validate_split_data(split_type, participants, split_data or {})
    
    # Calculate based on type
    if split_type == "equal":
        return calculate_equal_split(total_amount, participants)
    
    elif split_type == "exact":
        user_amounts = split_data["user_amounts"]
        return calculate_exact_split(total_amount, user_amounts)
    
    elif split_type == "percentage":
        user_percentages = split_data["user_percentages"]
        return calculate_percentage_split(total_amount, user_percentages)
    
    else:
        raise ValueError(f"Unknown split_type: {split_type}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_split_summary(splits: Dict[str, Decimal], paid_by: str) -> Dict:
    """
    Format split calculation into summary.
    
    Args:
        splits: Dict mapping user_id to share amount
        paid_by: User ID who paid
        
    Returns:
        Summary dict with payer and owes list
    """
    payer_amount = float(splits.get(paid_by, Decimal('0')))
    
    owes = []
    for user_id, amount in splits.items():
        if user_id != paid_by:
            owes.append({
                "user_id": user_id,
                "amount": float(amount)
            })
    
    return {
        "paid_by": paid_by,
        "paid_amount": payer_amount,
        "owes": owes
    }
