def get_user_domain(user_profile: dict) -> str:
    # Potential NoneType dereference
    email = user_profile.get('email')
    return email.split('@')[1]
