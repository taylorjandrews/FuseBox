# Taylor Andrews
#
# Key storage and retrieval
# Abstraction layer

import hashlib
import uuid
import random
import ConfigParser
from string import ascii_letters, digits
from pytutamen import utilities

# Return a key given a password and a salt
def get_salted_key(password, salt, key_length):
    return hashlib.sha256(password + salt).digest()[:key_length]

# Return a key given a password
def get_key(password, key_length):
    return hashlib.sha256(password).digest()[:key_length]

# Dummy function to create a key
def create_key():
    return ''.join(random.SystemRandom().choice(ascii_letters + digits) for i in range(32))

# Create external metadata
def create_data():
    # Fetch the default verifier
    cfile = open("./dropfuse.ini", 'r')
    config = ConfigParser.SafeConfigParser()
    config.read(cfile)

    verifiers = config.get('Tutamen', 'verifier')

    # Temporary measure to create the key
    key = create_key()

    # Store the key in a collection and secret
    suuid, cuuid, verifiers = utilities.store_secret(key, verifiers=verifiers)

    # Return the external metadata for new files
    return {"cuuid" : str(cuuid),  "suuid" : str(suuid), "size" : 0}

def retrieve_key(cuuid, suuid):
    return utilities.fetch_secret(uuid.UUID(suuid), uuid.UUID(cuuid))
