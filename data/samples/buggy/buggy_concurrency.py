import threading

counter = 0

def increment():
    global counter
    val = counter
    counter = val + 1
