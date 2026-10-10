import psycopg2
from psycopg2 import sql

# Import your existing settings
from app.config.config import settings  # Change this import to your actual settings module


def check_database():
    connection_params = {
        "host": settings.host,
        "port": settings.port,
        "user": settings.user,
        "password": settings.password,
        "dbname": settings.database_name,
        "connect_timeout": 5,
    }

    try:
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                # 1. Verify connection
                cur.execute("""
                    SELECT current_database(),
                           current_user,
                           version();
                """)
                database, user, version = cur.fetchone()

                print("✅ PostgreSQL connection successful!")
                print(f"Database: {database}")
                print(f"User: {user}")
                print(f"Version: {version.split(',')[0]}")

                # 2. List tables in the public schema
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """)
                tables = [row[0] for row in cur.fetchall()]

                if not tables:
                    print("\n⚠️ No tables found in the public schema.")
                    return

                print(f"\n📋 Found {len(tables)} table(s):")

                # 3. Count records in every table
                for table in tables:
                    cur.execute(
                        sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                            sql.Identifier("public"),
                            sql.Identifier(table),
                        )
                    )
                    count = cur.fetchone()[0]

                    print(f"\nTable: {table}")
                    print(f"Records: {count}")

                    # 4. Display up to five sample records
                    cur.execute(
                        sql.SQL("SELECT * FROM {}.{} LIMIT 5").format(
                            sql.Identifier("public"),
                            sql.Identifier(table),
                        )
                    )

                    columns = [desc.name for desc in cur.description]
                    rows = cur.fetchall()

                    print("Columns:", ", ".join(columns))
                    for row in rows:
                        print(" ", row)

    except psycopg2.OperationalError as exc:
        print(f"❌ Could not connect to PostgreSQL: {exc}")
    except psycopg2.Error as exc:
        print(f"❌ Database query failed: {exc}")


if __name__ == "__main__":
    check_database()
