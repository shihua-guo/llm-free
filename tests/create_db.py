import asyncio
import asyncpg
from config import settings

async def create_db():
    # Parse the DATABASE_URL to get host, user, password
    # URL format: postgresql+asyncpg://user:password@host:port/dbname
    url = settings.DATABASE_URL
    # Simplified parsing for this specific case
    parts = url.split("://")[1].split("@")
    user_pass = parts[0].split(":")
    user = user_pass[0]
    password = user_pass[1]
    
    host_port_db = parts[1].split("/")
    host_port = host_port_db[0].split(":")
    host = host_port[0]
    port = host_port[1]
    
    db_name = "llm_free"
    
    print(f"Connecting to {host}:{port} as {user} to create database {db_name}...")
    
    try:
        # Connect to 'postgres' database to create the new one
        conn = await asyncpg.connect(user=user, password=password, host=host, port=port, database='postgres')
        try:
            await conn.execute(f'CREATE DATABASE {db_name}')
            print(f"Database {db_name} created successfully.")
        except asyncpg.exceptions.DuplicateDatabaseError:
            print(f"Database {db_name} already exists.")
        finally:
            await conn.close()
    except Exception as e:
        print(f"Failed to create database: {e}")

if __name__ == "__main__":
    asyncio.run(create_db())
