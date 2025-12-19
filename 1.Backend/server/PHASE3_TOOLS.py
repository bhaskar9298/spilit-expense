# Phase 3 Tools - Add these to server.py before setup_database()

# Place this section before "# ADMIN TOOLS" section

# ============================================================================
# PHASE 3: MULTI-USER EXPENSE SPLITTING
# ============================================================================

@mcp.tool()
async def add_group_expense(
    user_id: str,
    group_id: str,
    amount: float,
    description: str,
    category: str,
    date: str,
    split_type: str,
    participants: list,
    user_amounts: dict = None,
    user_percentages: dict = None,
    subcategory: str = "",
    note: str = ""
):
    """
    Add an expense to a group with automatic splitting among participants.
    
    Split types:
    - "equal": Divide equally among all participants
    - "exact": Specific amounts for each (provide user_amounts)
    - "percentage": Percentage-based (provide user_percentages)
    """
    try:
        # Validate inputs
        if not validate_object_id(group_id):
            return {"status": "error", "message": "Invalid group ID format"}
        
        if not await is_user_in_group(user_id, group_id):
            return {"status": "error", "message": "Access denied: You are not a member of this group"}
        
        if amount <= 0:
            return {"status": "error", "message": "Amount must be greater than zero"}
        
        if split_type not in ["equal", "exact", "percentage"]:
            return {"status": "error", "message": "split_type must be 'equal', 'exact', or 'percentage'"}
        
        if not participants or len(participants) == 0:
            return {"status": "error", "message": "At least one participant is required"}
        
        if user_id not in participants:
            return {"status": "error", "message": "Payer must be included in participants"}
        
        # Validate all participants are group members
        for participant_id in participants:
            if not await is_user_in_group(participant_id, group_id):
                return {"status": "error", "message": f"Participant {participant_id} is not a member of this group"}
        
        # Prepare split data
        split_data = {}
        if split_type == "exact":
            if not user_amounts:
                return {"status": "error", "message": "user_amounts required for exact split"}
            split_data["user_amounts"] = user_amounts
        elif split_type == "percentage":
            if not user_percentages:
                return {"status": "error", "message": "user_percentages required for percentage split"}
            split_data["user_percentages"] = user_percentages
        
        # Calculate splits
        try:
            splits = calculate_splits(
                total_amount=amount,
                split_type=split_type,
                participants=participants,
                paid_by=user_id,
                split_data=split_data
            )
        except ValueError as ve:
            return {"status": "error", "message": f"Split calculation failed: {str(ve)}"}
        
        # Create expense document
        expense_doc = {
            "group_id": group_id,
            "paid_by": user_id,
            "user_id": user_id,
            "amount": float(amount),
            "description": description,
            "category": category,
            "subcategory": subcategory or "",
            "note": note or "",
            "date": date,
            "split_type": split_type,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert expense
        expense_result = await expenses_col.insert_one(expense_doc)
        expense_id = str(expense_result.inserted_id)
        
        # Create participant records
        participant_docs = []
        for participant_id, share_amount in splits.items():
            participant_doc = {
                "expense_id": expense_id,
                "user_id": participant_id,
                "share_amount": float(share_amount),
                "created_at": datetime.utcnow()
            }
            
            if split_type == "exact":
                participant_doc["exact_amount"] = float(user_amounts.get(participant_id, 0))
            elif split_type == "percentage":
                participant_doc["share_percentage"] = float(user_percentages.get(participant_id, 0))
            
            participant_docs.append(participant_doc)
        
        # Insert all participants
        await expense_participants_col.insert_many(participant_docs)
        
        # Format response
        expense_doc["id"] = expense_id
        del expense_doc["_id"]
        
        # Create split summary
        split_summary = []
        for participant_id, share_amount in splits.items():
            user = await users_col.find_one({"_id": ObjectId(participant_id)})
            split_summary.append({
                "user_id": participant_id,
                "email": user.get("email", "Unknown") if user else "Unknown",
                "full_name": user.get("full_name", "Unknown") if user else "Unknown",
                "share": float(share_amount),
                "is_payer": participant_id == user_id
            })
        
        return {
            "status": "success",
            "expense_id": expense_id,
            "expense": expense_doc,
            "splits": split_summary,
            "message": f"Expense added and split among {len(participants)} participants"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to add group expense: {str(e)}"}

@mcp.tool()
async def list_group_expenses(user_id: str, group_id: str, start_date: str = None, end_date: str = None):
    """
    List all expenses in a group with split details.
    """
    try:
        if not validate_object_id(group_id):
            return {"status": "error", "message": "Invalid group ID format"}
        
        if not await is_user_in_group(user_id, group_id):
            return {"status": "error", "message": "Access denied: You are not a member of this group"}
        
        # Build query
        query = {"group_id": group_id}
        if start_date and end_date:
            query["date"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            query["date"] = {"$gte": start_date}
        elif end_date:
            query["date"] = {"$lte": end_date}
        
        # Get expenses
        expenses = await expenses_col.find(query).sort("date", -1).to_list(None)
        
        if not expenses:
            return []
        
        # Get expense IDs
        expense_ids = [str(e["_id"]) for e in expenses]
        
        # Get all participants
        participants = await expense_participants_col.find({
            "expense_id": {"$in": expense_ids}
        }).to_list(None)
        
        # Group participants by expense
        participants_by_expense = {}
        for p in participants:
            expense_id = p["expense_id"]
            if expense_id not in participants_by_expense:
                participants_by_expense[expense_id] = []
            participants_by_expense[expense_id].append(p)
        
        # Get all user IDs
        all_user_ids = set()
        for e in expenses:
            all_user_ids.add(e.get("paid_by", e.get("user_id")))
        for p in participants:
            all_user_ids.add(p["user_id"])
        
        # Get user details
        users = await users_col.find({
            "_id": {"$in": [ObjectId(uid) for uid in all_user_ids if validate_object_id(uid)]}
        }).to_list(None)
        user_map = {str(u["_id"]): u for u in users}
        
        # Build response
        result = []
        for expense in expenses:
            expense_id = str(expense["_id"])
            paid_by = expense.get("paid_by", expense.get("user_id"))
            payer = user_map.get(paid_by, {})
            
            # Get participants for this expense
            expense_participants_list = participants_by_expense.get(expense_id, [])
            
            splits = []
            for p in expense_participants_list:
                participant_user = user_map.get(p["user_id"], {})
                splits.append({
                    "user_id": p["user_id"],
                    "email": participant_user.get("email", "Unknown"),
                    "full_name": participant_user.get("full_name", "Unknown"),
                    "share": p.get("share_amount", 0),
                    "is_payer": p["user_id"] == paid_by
                })
            
            expense_data = serialize(expense)
            expense_data["payer"] = {
                "user_id": paid_by,
                "email": payer.get("email", "Unknown"),
                "full_name": payer.get("full_name", "Unknown")
            }
            expense_data["splits"] = splits
            expense_data["participant_count"] = len(splits)
            
            result.append(expense_data)
        
        return result
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to list group expenses: {str(e)}"}

@mcp.tool()
async def get_expense_details(user_id: str, expense_id: str):
    """
    Get detailed information about a specific expense including all splits.
    """
    try:
        if not validate_object_id(expense_id):
            return {"status": "error", "message": "Invalid expense ID format"}
        
        # Get expense
        expense = await expenses_col.find_one({"_id": ObjectId(expense_id)})
        
        if not expense:
            return {"status": "error", "message": "Expense not found"}
        
        # Check access
        group_id = expense.get("group_id")
        if group_id:
            if not await is_user_in_group(user_id, group_id):
                return {"status": "error", "message": "Access denied"}
        else:
            if expense.get("user_id") != user_id and expense.get("paid_by") != user_id:
                return {"status": "error", "message": "Access denied"}
        
        # Get participants
        participants = await expense_participants_col.find({
            "expense_id": expense_id
        }).to_list(None)
        
        # Get user details
        if participants:
            user_ids = [ObjectId(p["user_id"]) for p in participants]
            users = await users_col.find({"_id": {"$in": user_ids}}).to_list(None)
            user_map = {str(u["_id"]): u for u in users}
            
            splits = []
            for p in participants:
                participant_user = user_map.get(p["user_id"], {})
                splits.append({
                    "user_id": p["user_id"],
                    "email": participant_user.get("email", "Unknown"),
                    "full_name": participant_user.get("full_name", "Unknown"),
                    "share": p.get("share_amount", 0),
                    "share_percentage": p.get("share_percentage"),
                    "exact_amount": p.get("exact_amount"),
                    "is_payer": p["user_id"] == expense.get("paid_by", expense.get("user_id"))
                })
        else:
            splits = []
        
        # Get payer details
        paid_by = expense.get("paid_by", expense.get("user_id"))
        payer = await users_col.find_one({"_id": ObjectId(paid_by)})
        
        expense_data = serialize(expense)
        expense_data["payer"] = {
            "user_id": paid_by,
            "email": payer.get("email", "Unknown") if payer else "Unknown",
            "full_name": payer.get("full_name", "Unknown") if payer else "Unknown"
        }
        expense_data["splits"] = splits
        expense_data["participant_count"] = len(splits)
        
        return expense_data
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to get expense details: {str(e)}"}
