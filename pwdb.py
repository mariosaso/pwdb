import os
import sys
import json
import sqlite3
import getpass
import base64
import bcrypt
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken
from InquirerPy import inquirer

SETTINGS_FILE = "settings.json"
DB_FILE = "pwdb.encrypted"

BANNER = r"""
           ..  
._ .    , _||_ 
[_) \/\/ (_][_)
|    

github.com/mariosasodotcom/pwdb
"""

class CryptoManager:
    """Handles master password hashing, key derivation, encryption and decryption."""
    def __init__(self, salt: bytes):
        self.salt = salt

    @staticmethod
    def hash_master_password(password: bytes) -> bytes:
        """Hash master password with bcrypt."""
        return bcrypt.hashpw(password, bcrypt.gensalt())

    def derive_key(self, password: bytes) -> bytes:
        """Derive a 32-byte encryption key from the master password using PBKDF2.
        Returns URL-safe base64-encoded key for Fernet."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100_000,
        )
        key = kdf.derive(password)
        return base64.urlsafe_b64encode(key)

    def encrypt(self, data: bytes, key: bytes) -> bytes:
        """Encrypt data with Fernet."""
        f = Fernet(key)
        return f.encrypt(data)

    def decrypt(self, token: bytes, key: bytes) -> bytes:
        """Decrypt data with Fernet; raises InvalidToken on failure."""
        f = Fernet(key)
        return f.decrypt(token)

class DBManager:
    """In-memory SQLite database manager with auto-persist to encrypted file."""
    def __init__(self, conn: sqlite3.Connection, crypto: CryptoManager, key: bytes):
        self.conn = conn
        self.crypto = crypto
        self.key = key
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                url TEXT,
                description TEXT,
                tag TEXT,
                password TEXT NOT NULL
            )
            '''
        )
        self.conn.commit()

    def add_entry(self, name: str, url: str, description: str, tag: str, password: str):
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO passwords (name, url, description, tag, password) VALUES (?, ?, ?, ?, ?)',
            (name, url, description, tag, password)
        )
        self.conn.commit()
        self._persist()

    def remove_entry(self, name: str):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM passwords WHERE name = ?', (name,))
        self.conn.commit()
        self._persist()

    def list_entries(self, filter_by: str = None) -> list:
        cur = self.conn.cursor()
        if filter_by:
            term = f"%{filter_by}%"
            cur.execute(
                'SELECT name, url, description, tag FROM passwords WHERE name LIKE ? OR tag LIKE ? ORDER BY name',
                (term, term)
            )
        else:
            cur.execute('SELECT name, url, description, tag FROM passwords ORDER BY name')
        return cur.fetchall()

    def get_password(self, name: str) -> str:
        cur = self.conn.cursor()
        cur.execute('SELECT password FROM passwords WHERE name = ?', (name,))
        row = cur.fetchone()
        return row[0] if row else None

    def _persist(self):
        """Dump memory DB to SQL script, encrypt, and write to disk."""
        dump = '\n'.join(self.conn.iterdump()).encode()
        token = self.crypto.encrypt(dump, self.key)
        with open(DB_FILE, 'wb') as f:
            f.write(token)

class UIManager:
    """Text-based UI using InquirerPy."""
    def __init__(self, db: DBManager):
        self.db = db

    def main_menu(self):
        while True:
            print()
            choice = inquirer.select(
                message="Select an action:",
                choices=[
                    'Add password',
                    'Remove password',
                    'View passwords',
                    'Exit'
                ],
                default=None
            ).execute()

            if choice == 'Add password':
                self.add_password()
            elif choice == 'Remove password':
                self.remove_password()
            elif choice == 'View passwords':
                self.view_passwords()
            elif choice == 'Exit':
                print("Goodbye!")
                sys.exit(0)

    def add_password(self):
        name = inquirer.text(message="Name:").execute()
        url = inquirer.text(message="URL:").execute()
        desc = inquirer.text(message="Description:", default="").execute()
        tag = inquirer.text(message="Tag:", default="").execute()
        pwd = inquirer.secret(message="Password (will be hidden):").execute()
        self.db.add_entry(name, url, desc, tag, pwd)
        print(f"Added entry '{name}'")

    def remove_password(self):
        entries = [row[0] for row in self.db.list_entries()]
        if not entries:
            print("No entries to remove.")
            return
        name = inquirer.select(message="Select entry to remove:", choices=entries).execute()
        self.db.remove_entry(name)
        print(f"Removed entry '{name}'")

    def view_passwords(self):
        term = inquirer.text(
            message="Filter by name or tag (leave empty for all):"
        ).execute()
        rows = self.db.list_entries(filter_by=term or None)
        if not rows:
            print("No matching entries.")
            return

        for name, url, description, tag in rows:
            print(f"- {name}")
            if url:
                print(f"    URL: {url}")
            if description:
                print(f"    Desc: {description}")
            if tag:
                print(f"    Tag: {tag}")

            # fetch and show password only if it exists
            pwd = self.db.get_password(name)
            if pwd:
                print(f"    Password: {pwd}")


def load_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        return {}
    with open(SETTINGS_FILE, 'r') as f:
        return json.load(f)

def save_settings(settings: dict):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

def setup_master_password():
    print("=== Initial Setup: Create a Master Password ===")
    while True:
        pwd1 = getpass.getpass("Enter new master password: ").encode()
        pwd2 = getpass.getpass("Re-enter to confirm: ").encode()
        if pwd1 != pwd2:
            print("Passwords do not match. Try again.")
        elif len(pwd1) < 8:
            print("Master password must be at least 8 characters.")
        else:
            break
    salt = os.urandom(16)
    hash_pw = CryptoManager.hash_master_password(pwd1)
    settings = {
        'master_hash': hash_pw.decode(),
        'salt': base64.b64encode(salt).decode()
    }
    save_settings(settings)
    # Initialize empty encrypted DB
    crypto = CryptoManager(salt)
    key = crypto.derive_key(pwd1)
    conn = sqlite3.connect(':memory:')
    DBManager(conn, crypto, key)
    print("Setup complete. Encrypted database created.")

def main():
    print(BANNER)
    settings = load_settings()
    if not settings:
        setup_master_password()
        settings = load_settings()
    master = getpass.getpass("Enter master password: ").encode()
    salt = base64.b64decode(settings['salt'])
    crypto = CryptoManager(salt)
    stored_hash = settings['master_hash'].encode()
    if not bcrypt.checkpw(master, stored_hash):
        print("Incorrect master password. Exiting.")
        sys.exit(1)
    key = crypto.derive_key(master)
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'rb') as f:
            token = f.read()
        try:
            dump = crypto.decrypt(token, key)
        except InvalidToken:
            print("Failed to decrypt database. Exiting.")
            sys.exit(1)
        conn = sqlite3.connect(':memory:')
        conn.executescript(dump.decode())
    else:
        conn = sqlite3.connect(':memory:')
    db = DBManager(conn, crypto, key)
    ui = UIManager(db)
    ui.main_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye :)")
