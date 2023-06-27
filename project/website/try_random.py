import random
import string

def generate_user_id():
    letters = string.ascii_uppercase
    digits = string.digits

    # Generate the first 2 characters as uppercase alphabets
    first_part = ''.join(random.choice(letters) for _ in range(2))

    # Generate the ninth character as an uppercase alphabet
    ninth_character = random.choice(letters)

    # Generate the remaining 6 characters as numbers
    second_part = ''.join(random.choice(digits) for _ in range(6))
    
    # Generate the last character as number
    last_character = random.choice(digits)

    user_id = f"{first_part}{second_part}{ninth_character}{last_character}"
    
    return user_id

print(generate_user_id())