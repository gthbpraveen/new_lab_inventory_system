from app import app, db
from models import populate_room_and_cubicles

with app.app_context():
    populate_room_and_cubicles(force=True)
    print("Rooms and cubicles populated successfully!")
