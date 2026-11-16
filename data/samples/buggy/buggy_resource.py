def read_and_count_lines(filepath: str) -> int:
    # Resource leak: file is never closed
    f = open(filepath, 'r')
    lines = f.readlines()
    return len(lines)
