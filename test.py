import bcrypt

def generate_hash(password):
    """Generate a bcrypt hash for manual DB insertion"""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

# === Change the password here ===
password = "admin123"

hashed = generate_hash(password)
print(f"Password:  {password}")
print(f"Hash:      {hashed}")
print()
print("-- SQL to insert/update --")
print(f"UPDATE users SET hashed_password = '{hashed}' WHERE email = 'admin@company.com';")
