import random

def generate_random_password():
	characters = "1234567890QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm"
	length = 12

	return "".join([random.choice(characters) for _ in range(length)])