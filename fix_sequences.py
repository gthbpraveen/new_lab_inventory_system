from app import app
from models import db
from sqlalchemy import text

def reset_all_sequences():
    with app.app_context():
        # Get all tables and their serial/identity columns
        seq_query = text("""
            SELECT
                table_name,
                column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND column_default LIKE 'nextval%%'
        """)
        results = db.session.execute(seq_query).fetchall()

        if not results:
            print("⚠️ No sequences found in public schema.")
            return

        for table, column in results:
            reset_sql = text(f"""
                SELECT setval(
                    pg_get_serial_sequence('"{table}"', '{column}'),
                    COALESCE((SELECT MAX("{column}") FROM "{table}"), 1) + 1,
                    false
                )
            """)
            try:
                db.session.execute(reset_sql)
                print(f"✅ Reset sequence for {table}.{column}")
            except Exception as e:
                print(f"⚠️ Failed for {table}.{column}: {e}")

        db.session.commit()
        print("🎉 All sequences reset successfully")

if __name__ == "__main__":
    reset_all_sequences()
