from cryptography.fernet import Fernet

"""
class Config:
    SECRET_KEY = "clavE sEGURa"

NEO4J_URI=neo4j+s://f03zb879.databases.neo4j.io
"""

def read_key():
    return open("./_neo4j/keyfile.key","rb").read()


class Config:    
    URI = "neo4j+s://f03ab659.databases.neo4j.io"
    USERNAME="neo4j"


def get_pass(username):
    key = read_key()
    # inicializar fernet
    fern=Fernet(key)
    with open("./_neo4j/key_pass_file.key","rb") as fbo:
        msg_encripreadit = fbo.read()
    #desencriptar
    msg_ori2 = fern.decrypt(msg_encripreadit).decode()
    print(f"\n\nfrom encrypted pass") # : {msg_ori2}")
    return msg_ori2
            

class Config:    
    URI = "neo4j+s://f03ab659.databases.neo4j.io"
    USERNAME="neo4j"
    
