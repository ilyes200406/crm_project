def can_modify_opportunity(user, opportunity):
    if user.role == 'ADMIN':
        return True
    
    if user.role == 'COMMERCIAL':
        return (
            opportunity.created_by == user or
            opportunity.assigned_to == user
        )
    
    return False