import os
import uuid
from sqlalchemy import create_engine, Column, Integer, String, Table, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


user = os.getenv("pg_user", "postgres")
password = os.getenv("pg_password")
host = os.getenv("pg_host", "localhost")
port = os.getenv("pg_port", "5432")
dbname = os.getenv("pg_database", "ChAIn-Reaction")

DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Association table for many-to-many between users and repos
user_repos = Table(
    "user_repos",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("repo_id", String, ForeignKey("repos.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)

    repos = relationship("Repo", secondary=user_repos, back_populates="users")


class Repo(Base):
    __tablename__ = "repos"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    url = Column(String, nullable=False, unique=True)

    users = relationship("User", secondary=user_repos, back_populates="repos")


def create_tables():
    Base.metadata.create_all(bind=engine)


class UserRepository:
    def __init__(self):
        self._Session = SessionLocal

    def create_user(self, username: str, name: str, password: str):
        session = self._Session()
        try:
            user = User(username=username, name=name, password=password)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def get_user_by_username(self, username: str):
        session = self._Session()
        try:
            return session.query(User).filter(User.username == username).first()
        finally:
            session.close()

    def get_user_by_id(self, user_id: int):
        session = self._Session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()

    def add_repo_to_user(self, user_id: int, repo_url: str, repo_name: str):
        """Add a repo to a user. Returns {"id": ..., "repo_name": ..., "repo_url": ..., "is_new": bool}.
        
        - If repo doesn't exist: creates it, maps to user, is_new=True
        - If repo exists but not mapped: maps to user, is_new=False
        - If repo exists and already mapped: no change, is_new=False (safe from duplicates)
        """
        session = self._Session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            repo = session.query(Repo).filter(Repo.url == repo_url).first()
            is_new = False
            if not repo:
                repo = Repo(url=repo_url, name=repo_name)
                session.add(repo)
                session.flush()
                is_new = True
            else:
                # update name if provided and missing or different
                if repo_name and repo.name != repo_name:
                    repo.name = repo_name
                    session.add(repo)
                    session.flush()

            # only add mapping if repo is not already in user.repos (prevents duplicates)
            if repo not in user.repos:
                user.repos.append(repo)
                session.add(user)
                session.commit()
                session.refresh(user)

            return {
                "id": repo.id,
                "repo_name": repo.name,
                "repo_url": repo.url,
                "is_new": is_new,
            }
        finally:
            session.close()

    def get_user_profile(self, user_id: int):
        session = self._Session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            return {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "repos": [{"id": r.id, "name": r.name, "url": r.url} for r in user.repos],
            }
        finally:
            session.close()
