"""
This program generates the keys that we will use to encrypt 
delicate data
make sure to use it only once per item, to avoid overwriting 
other keys
"""

from cryptography.fernet import Fernet

def write_key(which):
    """
    Generates a key and stores itin a file
    """
    key = Fernet.generate_key()
    with open("keys/"+ which + ".key", "wb") as key_file:
        key_file.write(key)
        
for which in ["db", "tokens"]: # one key for the databases, one key for the bot tokens
    write_key(which)
