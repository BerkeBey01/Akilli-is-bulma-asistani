import os
from app import app
from extensions import db
import models 

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'proje.db')

if os.path.exists(db_path):
    os.remove(db_path)

with app.app_context():
    db.create_all()
    print("Veritabanı başarıyla oluşturuldu.")