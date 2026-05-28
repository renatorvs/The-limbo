try:
    import bcrypt
    
    password = "short"
    print(f"Hashing password: '{password}'")
    # bcrypt requires bytes
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    print(f"Hash: {hashed}")
    
    check = bcrypt.checkpw(password.encode('utf-8'), hashed)
    print(f"Check: {check}")

    password = "validpassword123"
    print(f"Hashing password: '{password}'")
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    print(f"Hash: {hashed}")
    check = bcrypt.checkpw(password.encode('utf-8'), hashed)
    print(f"Check: {check}")
    
    print("✅ Bcrypt Direct Usage Works")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"❌ Error: {e}")
