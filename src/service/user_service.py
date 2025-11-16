import os
import datetime
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from src.repository.user_repository import UserRepository, create_tables
from src.util.logger import log

SECRET_KEY = os.environ.get("JWT_SECRET", "change-me-secret")
TOKEN_EXP_SECONDS = int(os.environ.get("JWT_EXP_SECONDS", "86400"))


class UserService:
    def __init__(self):
        # ensure tables exist
        try:
            create_tables()
        except Exception:
            log.warning("Could not create tables on init; ensure DB is reachable")

        self.repo = UserRepository()

    def signup(self, username: str, name: str, password: str):
        existing = self.repo.get_user_by_username(username)
        if existing:
            return {"error": "username already exists"}, 400

        hashed = generate_password_hash(password)
        user = self.repo.create_user(username=username, name=name, password=hashed)
        return {"id": user.id, "username": user.username, "name": user.name}

    def login(self, username: str, password: str):
        user = self.repo.get_user_by_username(username)
        if not user:
            return {"error": "invalid credentials"}, 401

        if not check_password_hash(user.password, password):
            return {"error": "invalid credentials"}, 401

        payload = {
            "sub": str(user.id),
            "iat": datetime.datetime.utcnow(),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=TOKEN_EXP_SECONDS),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        if isinstance(token, bytes):
            token = token.decode("utf-8")
        profile = self.get_profile(user.id)
        return {"token": token, "profile": profile}

    def decode_token(self, token: str):
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            sub = data.get("sub")
            if isinstance(sub, str):
                try:
                    data["sub"] = int(sub)
                except ValueError:
                    pass
            return data
        except jwt.ExpiredSignatureError:
            return {"error": "token_expired"}
        except Exception as e:
            log.warning(f"token decode error: {e}")
            return {"error": "invalid_token"}

    def get_profile(self, user_id: int):
        return self.repo.get_user_profile(user_id)

    def add_repository_to_user(self, user_id: int, repo_url: str, repo_name: str):
        repo = self.repo.add_repo_to_user(user_id, repo_url, repo_name)
        if not repo:
            return {"error": "user not found"}, 404
        return repo