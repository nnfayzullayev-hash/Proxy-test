import asyncpg

import config


class Database:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            min_size=1,
            max_size=10,
        )
        await self.init_models()

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def init_models(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS news (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                card_number TEXT DEFAULT '',
                nickname TEXT DEFAULT '',
                CHECK (id = 1)
            );

            CREATE TABLE IF NOT EXISTS tests (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                pdf_file_id TEXT,
                start_time TIMESTAMP,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS tickets (
                id SERIAL PRIMARY KEY,
                ticket_code TEXT UNIQUE NOT NULL,
                user_id INTEGER REFERENCES users(id),
                test_id INTEGER REFERENCES tests(id),
                status TEXT DEFAULT 'unused',
                created_at TIMESTAMP DEFAULT NOW(),
                used_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS submissions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                test_id INTEGER REFERENCES tests(id),
                ticket_id INTEGER REFERENCES tickets(id),
                content_type TEXT,
                file_id TEXT,
                text_content TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """)
            await conn.execute(
                "INSERT INTO settings (id) VALUES (1) ON CONFLICT (id) DO NOTHING"
            )

    # ---------- USERS ----------
    async def get_or_create_user(self, telegram_id, first_name, last_name, username):
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE telegram_id=$1", telegram_id)
            if user:
                return user
            return await conn.fetchrow(
                """INSERT INTO users (telegram_id, first_name, last_name, username)
                   VALUES ($1,$2,$3,$4) RETURNING *""",
                telegram_id, first_name, last_name, username
            )

    async def get_user_by_telegram_id(self, telegram_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM users WHERE telegram_id=$1", telegram_id)

    async def get_user_by_id(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM users WHERE id=$1", user_id)

    async def count_users(self):
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM users")

    # ---------- NEWS ----------
    async def add_news(self, title, text):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "INSERT INTO news (title, text) VALUES ($1,$2) RETURNING *", title, text
            )

    async def get_news_list(self, limit=10):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM news ORDER BY created_at DESC LIMIT $1", limit)

    async def delete_news(self, news_id):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM news WHERE id=$1", news_id)

    # ---------- SETTINGS ----------
    async def get_settings(self):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM settings WHERE id=1")

    async def set_card_number(self, value):
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE settings SET card_number=$1 WHERE id=1", value)

    async def set_nickname(self, value):
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE settings SET nickname=$1 WHERE id=1", value)

    # ---------- TESTS ----------
    async def create_test(self, name, description, pdf_file_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """INSERT INTO tests (name, description, pdf_file_id, status)
                   VALUES ($1,$2,$3,'draft') RETURNING *""",
                name, description, pdf_file_id
            )

    async def set_test_time(self, test_id, start_time):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """UPDATE tests SET start_time=$2, status='active'
                   WHERE id=$1 RETURNING *""",
                test_id, start_time
            )

    async def get_test(self, test_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM tests WHERE id=$1", test_id)

    async def list_tests(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM tests ORDER BY id DESC")

    # ---------- TICKETS ----------
    async def create_ticket(self, ticket_code, user_id, test_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """INSERT INTO tickets (ticket_code, user_id, test_id, status)
                   VALUES ($1,$2,$3,'unused') RETURNING *""",
                ticket_code, user_id, test_id
            )

    async def ticket_code_exists(self, ticket_code):
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT 1 FROM tickets WHERE ticket_code=$1", ticket_code)

    async def get_ticket_by_code(self, ticket_code):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM tickets WHERE ticket_code=$1", ticket_code)

    async def mark_ticket_used(self, ticket_id):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE tickets SET status='used', used_at=NOW() WHERE id=$1", ticket_id
            )

    async def list_tickets(self, limit=30):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM tickets ORDER BY created_at DESC LIMIT $1", limit)

    # ---------- SUBMISSIONS ----------
    async def create_submission(self, user_id, test_id, ticket_id, content_type, file_id, text_content):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """INSERT INTO submissions (user_id, test_id, ticket_id, content_type, file_id, text_content)
                   VALUES ($1,$2,$3,$4,$5,$6) RETURNING *""",
                user_id, test_id, ticket_id, content_type, file_id, text_content
            )

    async def list_submissions(self, limit=20):
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM submissions ORDER BY created_at DESC LIMIT $1", limit
            )


db = Database()
