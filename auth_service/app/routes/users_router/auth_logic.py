from passlib.context import CryptContext


class PasswordSettings:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get_password_hash(self, password: str) -> str:
        hash_result = self.pwd_context.hash(password)
        print(f"DEBUG: Generated hash: {hash_result}")
        print(f"DEBUG: Hash length: {len(hash_result)}")
        return hash_result

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        print("DEBUG verify_password called:")
        print(
            f"  Plain password: {'*' * len(plain_password) if plain_password else 'EMPTY'}"
        )
        print(f"  Hashed password: {hashed_password}")
        print(f"  Hashed password type: {type(hashed_password)}")
        print(
            f"  Hashed password length: {len(hashed_password) if hashed_password else 0}"
        )

        if not hashed_password:
            print("ERROR: Hashed password is empty or None!")
            return False

        if not isinstance(hashed_password, str):
            print(
                f"ERROR: Hashed password is not a string! Type: {type(hashed_password)}"
            )
            return False

        # Попробуем определить формат хэша
        try:
            from passlib.hash import bcrypt

            print(f"DEBUG: Is bcrypt hash? {bcrypt.identify(hashed_password)}")
        except:
            pass

        try:
            result = self.pwd_context.verify(plain_password, hashed_password)
            print(f"DEBUG: Verification result: {result}")
            return result
        except Exception as e:
            print(f"ERROR in verify_password: {type(e).__name__}: {e}")
            # Попробуем проверить, является ли это валидным bcrypt хэшем
            if hashed_password:
                print(f"DEBUG: First 30 chars of hash: {hashed_password[:30]}")
                print(
                    f"DEBUG: Hash starts with $2b$? {hashed_password.startswith('$2b$')}"
                )
                print(
                    f"DEBUG: Hash starts with $2a$? {hashed_password.startswith('$2a$')}"
                )
                print(
                    f"DEBUG: Hash starts with $2y$? {hashed_password.startswith('$2y$')}"
                )
            return False


pass_settings = PasswordSettings()
