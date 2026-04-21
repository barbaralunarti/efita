# backend/seed_admin.py
"""Script para criar o admin inicial. Execute uma vez antes de iniciar o servidor."""
import sys
import os

# Garante que o módulo app seja encontrado
sys.path.insert(0, os.path.dirname(__file__))

from app.auth import hash_password
from app.database import SessionLocal, engine
from app.models import Admin, Base


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        username = input("Username do admin [admin]: ").strip() or "admin"
        password = input("Senha do admin: ").strip()
        if not password:
            print("Senha não pode ser vazia.")
            sys.exit(1)

        existing = db.query(Admin).filter(Admin.username == username).first()
        if existing:
            print(f"Admin '{username}' já existe.")
            return

        admin = Admin(username=username, password_hash=hash_password(password))
        db.add(admin)
        db.commit()
        print(f"Admin '{username}' criado com sucesso!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
