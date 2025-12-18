import sqlite3

def setup_database():
    conn = sqlite3.connect('conference_bot.db')
    cursor = conn.cursor()

    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(20) NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS users (
        tg_id INTEGER PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        role VARCHAR(20) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_tg_id INTEGER NOT NULL,
        group_id INTEGER NOT NULL,
        FOREIGN KEY (user_tg_id) REFERENCES users(tg_id) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
        UNIQUE (user_tg_id, group_id)
    );

    CREATE TABLE IF NOT EXISTS conferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic VARCHAR(100) NOT NULL,
        conf_date TEXT NOT NULL,
        conf_time TEXT NOT NULL,
        link TEXT NOT NULL,
        group_id INTEGER NOT NULL,
        FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
    );
    ''')

    try:
        cursor.executescript('''
        INSERT OR IGNORE INTO groups (name) VALUES 
        ('G-1'), ('АД-2024'), ('QA-Automation'), ('DevOps-Night'), 
        ('PM-Basic'), ('Java-Pro'), ('Design-UI'), ('HR-Management'), 
        ('Cyber-Sec'), ('Group_Limit_20_Char');

        INSERT OR IGNORE INTO users (tg_id, username, role) VALUES 
        (101, 'admin_alex', 'admin'),
        (201, 'user_ivan', 'student'),
        (301, 'teacher_olga', 'teacher'),
        (401, 'student_petro', 'student'),
        (501, 'guest_user', 'student');

        INSERT OR IGNORE INTO group_members (user_tg_id, group_id) VALUES 
        (201, 1), (201, 3), (301, 6), (401, 1);

        INSERT OR IGNORE INTO conferences (topic, conf_date, conf_time, link, group_id) VALUES 
        ('Вступ до мереж', '25.12.2025', '10:00', 'https://zoom.us/j/101', 1),
        ('Git Flow', '22.12.2024', '12:30', 'https://meet.google.com/aaa', 3);
        ''')
        print("База даних успішно ініціалізована!")
    except sqlite3.Error as e:
        print(f"Виникла помилка: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()