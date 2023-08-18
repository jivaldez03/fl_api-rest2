from cryptography.fernet import Fernet

"""
class Config:
    SECRET_KEY = "clavE sEGURa"

NEO4J_URI=neo4j+s://f03zb879.databases.neo4j.io
"""

def kodb():
    with open("./_neo4j/service_active.txt","r") as kos:
        service = kos.read()
        service_value = int(service.split(";")[0])
        #print("service_active->", service_value)
        #input ("cr to continue")
    return service_value #1 # 1 = dev / 2 = prod

def read_key():
    return open("./_neo4j/file.yek","rb").read()


class Config:    
    URI = "neo4j+s://f03ab659.databases.neo4j.io:7687"
    #URI = "bolt+s://f03ab659.databases.neo4j.io:7687"
    USERNAME="neo4j"

class Configp:
    #URI = "neo4j+s://f03ab659.databases.neo4j.io"
    URI = "neo4j+s://27fa89f2.databases.neo4j.io:7687"
    #URI = "bolt+s://27fa89f2.databases.neo4j.io"
    USERNAME="neo4j"
    

def get_pass(username):
    key = read_key()
    # inicializar fernet
    fern=Fernet(key)
    if kodb() == 1:
        with open("./_neo4j/kfile.yek","rb") as fbo:
            msg_encripreadit = fbo.read()
    elif kodb() == 2:
        with open("./_neo4j/kfilep.yek","rb") as fbo:
            msg_encripreadit = fbo.read()
    else:
        msg_encripreadit = None
    #desencriptar
    msg_ori2 = fern.decrypt(msg_encripreadit).decode()
    #print(f"\n\nfrom encrypted pass") # : {msg_ori2}")
    return msg_ori2
     