import hashlib
import uuid
from passlib.context import CryptContext


pwd_cxt = CryptContext(schemes=["bcrypt"],deprecated = "auto")

class Hash():
       
    
    async def sha256(data: str):
        # Create a SHA-256 hash object
        sha256_hash = hashlib.sha256()
        # Ensure the input data is encoded to bytes before hashing
        sha256_hash.update(data.encode('utf-8'))
        # Return the hexadecimal representation of the hash
        return sha256_hash.hexdigest()
    
    async def uuid():
          # Generate a random UUID4
            random_uuid = uuid.uuid4()
            # Convert to hex and hash
            hashed_uuid = hashlib.sha256(str(random_uuid).encode()).hexdigest()[:16]
            
            return hashed_uuid
    
    #Creating Hash
    async def bcrypt(password: str):
        return pwd_cxt.hash(password)
    
    #Validating Hash
    async def verify_pass(plain_password, hashed_password):
        return pwd_cxt.verify(plain_password, hashed_password)
    
