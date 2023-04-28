"""
this program encrypts a static file (once)
"""

from cryptography.fernet import Fernet

def encrypt(filename, key):
    """
    Given a filename (str) and key (bytes), it encrypts the file and writes it
    """
    f = Fernet(key)
    # read file
    with open(filename, "rb") as file:
        # read all file data
        file_data = file.read()
    # encrypt data
    encrypted_data = f.encrypt(file_data)
    # write the encrypted file
    with open(filename, "wb") as file:
        file.write(encrypted_data)
       
def load_key():
    """
    Loads the key 
    """
    key = open("keys/" + which + ".key", "rb").read()
    return key

key = open("keys/tokens.key", "rb").read()
encrypt("../tokens.json", key)
