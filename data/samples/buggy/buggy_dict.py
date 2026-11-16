def extract_nested_token(config: dict) -> str:
    # Unsafe chained dict lookup
    return config['auth']['tokens']['jwt']
