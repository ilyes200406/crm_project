def can_modify_opportunity(user, opportunity):
    if user.role_id == 'ADMIN':
        return True
    
    if user.role_id == 'COMMERCIAL':
        return (
            opportunity.created_by == user or
            opportunity.assigned_to == user
        )
    
    return False