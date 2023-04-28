"""
reads a file formerly encrypted by python
decrypts it and gives back the content of the file
"""

from cryptography.fernet import Fernet

def decrypt(filename, key):
    """
    Given a filename (str) and key (bytes), it decrypts the file and write it
    """
    f = Fernet(key)
    with open(filename, "rb") as file:
        # read the encrypted data
        encrypted_data = file.read()
    # decrypt data
    decrypted_data = f.decrypt(encrypted_data)
    return decrypted_data

"""
import json
key = open("keys/tokens.key", "rb").read()
data = json.loads(decrypt("../tokens.json", key))
data["CoAct_at_SDG"] = ""

print(data)

with open('data.json', 'w') as fp:
    json.dump(data, fp)
"""
