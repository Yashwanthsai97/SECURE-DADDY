# SecureDaddy

## MySQL setup

1. Create a `.env` file in the project root with:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=secure_daddy
```

2. Install dependencies:

```powershell
.\.venv\Scripts\pip install -r requirements.txt
```

3. Start MySQL and run the app:

```powershell
.\.venv\Scripts\python app.py
```

The application will automatically create the `secure_daddy` database and the `users` table on startup.

### Optional auto-start of local MySQL on Windows

If MySQL is installed on a laptop as a Windows service, `app.py` can try to start it automatically before connecting.

Add these to `.env`:

```env
MYSQL_AUTO_START_SERVICE=true
MYSQL_WINDOWS_SERVICE_NAME=MySQL80
```

Notes:
- This only works if MySQL is already installed on that laptop.
- It is meant for local use on each friend's machine.
- It does not install MySQL automatically; it only tries to start an existing Windows service.

## One-time migration from `users.json`

If you want to import existing JSON users into MySQL first, run:

```powershell
.\.venv\Scripts\python scripts\migrate_users_json_to_mysql.py
```

Migrated accounts keep their existing password hash temporarily and are upgraded to bcrypt automatically after the next successful login.

## SQL to create the table manually

```sql
CREATE DATABASE IF NOT EXISTS secure_daddy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE secure_daddy;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    password_algorithm VARCHAR(32) NOT NULL DEFAULT 'bcrypt',
    role VARCHAR(255) NOT NULL DEFAULT 'Security Analyst',
    company VARCHAR(255) NOT NULL DEFAULT 'Independent Research',
    location VARCHAR(255) NOT NULL DEFAULT 'Hyderabad, India',
    focus_area VARCHAR(255) NOT NULL DEFAULT 'OSINT & Metadata Analysis',
    bio TEXT,
    website VARCHAR(512) NOT NULL DEFAULT '',
    headline VARCHAR(255) NOT NULL DEFAULT 'Security analyst building practical cyber workflows.',
    profile_picture MEDIUMTEXT,
    facebook_url VARCHAR(512) NOT NULL DEFAULT '',
    instagram_url VARCHAR(512) NOT NULL DEFAULT '',
    linkedin_url VARCHAR(512) NOT NULL DEFAULT '',
    tiktok_url VARCHAR(512) NOT NULL DEFAULT '',
    x_url VARCHAR(512) NOT NULL DEFAULT '',
    youtube_url VARCHAR(512) NOT NULL DEFAULT '',
    show_profile_to_logged_in_users TINYINT(1) NOT NULL DEFAULT 1,
    show_activity_on_profile TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP
);
```
