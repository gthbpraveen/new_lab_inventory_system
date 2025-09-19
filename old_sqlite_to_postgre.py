#!/usr/bin/env python3
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import (
    User, Student, Equipment, EquipmentHistory,
    WorkstationAsset, WorkstationAssignment,
    ProvisioningRequest, RoomLab, Cubicle, SlurmAccount
)

# --- CONFIG ---
sqlite_path = "/home/praveen/GPK/Lab-and-inventory-system/instance/database.db"
sqlite_url = f"sqlite:///{sqlite_path}"
postgres_url = "postgresql://lab_user:admin@localhost/lab_inventory"

# --- ENGINES ---
sqlite_engine = create_engine(sqlite_url)
postgres_engine = create_engine(postgres_url)

SQLiteSession = sessionmaker(bind=sqlite_engine)
PostgresSession = sessionmaker(bind=postgres_engine)

sqlite_sess = SQLiteSession()
pg_sess = PostgresSession()


def migrate_table(model):
    """Copy all records from SQLite to PostgreSQL for a given model."""
    print(f"➡ Migrating {model.__tablename__} ...", end=" ")
    records = sqlite_sess.query(model).all()
    for record in records:
        # Turn into dictionary
        data = {col.name: getattr(record, col.name) for col in model.__table__.columns}
        # Insert into Postgres
        pg_sess.merge(model(**data))
    pg_sess.commit()
    print(f"done ({len(records)} rows)")


def main():
    try:
        migrate_table(User)
        migrate_table(Student)
        migrate_table(RoomLab)
        migrate_table(Cubicle)
        migrate_table(WorkstationAsset)
        migrate_table(WorkstationAssignment)
        migrate_table(Equipment)
        migrate_table(EquipmentHistory)
        migrate_table(ProvisioningRequest)
        migrate_table(SlurmAccount)

        print("✅ Migration finished successfully!")

    except Exception as e:
        print("❌ Error during migration:", e)
        pg_sess.rollback()

    finally:
        sqlite_sess.close()
        pg_sess.close()


if __name__ == "__main__":
    main()
