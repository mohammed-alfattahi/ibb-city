import sqlite3

db_path = 'db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Delete from django_migrations
cursor.execute("DELETE FROM django_migrations WHERE app='bookings'")
print(f"Deleted {cursor.rowcount} rows from django_migrations for 'bookings'")

# 2. Drop tables
tables = [
    'bookings_bookingstatushistory',
    'bookings_booking',
    'bookings_availabilityslot',
    'bookings_bookableservice',
]

for table in tables:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"Dropped table {table}")
    except Exception as e:
        print(f"Error dropping {table}: {e}")

conn.commit()
conn.close()
print("Bookings app reset complete.")
