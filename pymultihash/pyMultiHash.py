"""
pyMultihash is a python implementation of the Multihash standard: https://github.com/jbenet/multihash

"""

import hashlib
from . import base58


"""
These first two methods are kinda inefficient, but python is not really designed to mess with bytes
"""
def int_to_byte_array(big_int):
    array = []
    while big_int > 1:
        array.append(big_int%256)
        big_int//=256
    return array

def bytes_to_long(bytestr):
    assert(len(bytestr)>0)
    return int( ''.join('{:02x}'.format(x) for x in bytestr), 16)


"""
    the main event!
"""
def parseHash(hashstr):
    hashint = base58.decode(hashstr)
    hashbytes = int_to_byte_array(hashint)
    if len(hashbytes) < 3:
        raise Exception("Multihash must be at least 3 bytes")

    hash_func_id = hashbytes[0]
    hash_length = int(hashbytes[1])
    hash_contents = hashbytes[2:hash_length+2]

    return bytes_to_long(hash_contents)

def genHash(bytestr,func_id):
    hashfunc = None
    if func_id == 0x11:
        #function is sha1
        hashfunc = hashlib.sha1()
    elif func_id == 0x12:
        #function is sha256
        hashfunc = hashlib.sha256()
    elif func_id == 0x13:
        #function is sha512
        hashfunc = hashlib.sha512()
    else:
        raise Exception("Requested hash is not supported")
    bytestr = bytearray(bytestr,"UTF-8")
    hashfunc.update(bytestr)
    data = hashfunc.digest()
    size = hashfunc.digest_size
    bytes = [func_id,size]+list(data)
    return base58.encode(bytes_to_long(bytes))

