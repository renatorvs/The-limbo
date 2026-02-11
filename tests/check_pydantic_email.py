from pydantic import BaseModel, EmailStr

try:
    class User(BaseModel):
        email: EmailStr
    
    u = User(email="test@example.com")
    print("✅ Pydantic Email Validation Works")
except ImportError as e:
    print(f"❌ ImportError: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
