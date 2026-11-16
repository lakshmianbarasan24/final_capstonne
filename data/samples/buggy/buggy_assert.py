def verify_admin_access(user: dict):
    # Security risk: assert removed under Python -O
    assert user.get('is_admin') is True, 'Access Denied'
    return True
