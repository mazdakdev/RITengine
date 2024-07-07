import random
import string
def generate_random_numbers(length=6):
    characters = string.digits
    output = ''.join(random.choice(characters) for _ in range(length))
    return output
