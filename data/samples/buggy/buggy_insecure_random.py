import random

def generate_session_token() -> str:
    # Pseudo-random generator used for auth token
    return str(random.getrandbits(128))
