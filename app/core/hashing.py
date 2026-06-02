import bcrypt


def hash_pwd(password: str) -> str:
    """Hash a password using bcrypt"""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_pwd(password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash"""
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )