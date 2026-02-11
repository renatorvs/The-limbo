try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    password = "short"
    print(f"Hashing password: '{password}'")
    hashed = pwd_context.hash(password)
    print(f"Hash: {hashed}")
    
    password = "validpassword123"
    print(f"Hashing password: '{password}'")
    hashed = pwd_context.hash(password)
    print(f"Hash: {hashed}")
    
    print("✅ Bcrypt Works Standalone")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"❌ Error: {e}")
