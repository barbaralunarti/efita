import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.auth import hash_password
from app.database import SessionLocal, engine
from app.models import Admin, Base

Base.metadata.create_all(bind=engine)
db = SessionLocal()
existing = db.query(Admin).filter(Admin.username == "admin").first()
if not existing:
    admin = Admin(username="admin", password_hash=hash_password("admin"))
    db.add(admin)
    db.commit()
    print("Admin 'admin' criado com sucesso com senha 'admin'")
else:
    # força a senha admin
    existing.password_hash = hash_password("admin")
    db.commit()
    print("Admin 'admin' atualizado com senha 'admin'")
db.close()
