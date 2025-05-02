# 🗝️ pwdb — Encrypted Terminal Password Manager

> A lightweight, encrypted password manager for your terminal — no cloud, no clipboard, no bloat.

---

## 🔐 Features

- Secure password encryption using:
  - `Fernet` (AES-based symmetric encryption)
  - Key derived with PBKDF2-HMAC-SHA256
  - Master password protected with bcrypt
- Encrypted SQLite database dumped to disk (`pwdb.encrypted`)
- Fully terminal-based UI via [InquirerPy](https://github.com/kazhala/InquirerPy)
- No clipboard interaction (privacy by design)
- Fully offline — works even without internet
- Free and open-source under GNU GPLv3

---

## 🚀 Usage

```bash
git clone https://github.com/mariosasodotcom/pwdb
cd pwdb
python pwdb.py
```

> Required Python packages:
> - `bcrypt`
> - `cryptography`
> - `InquirerPy`

---

First time? You’ll be prompted to set a master password. After that:

### 🔍 Main Menu Options

- **Add password** — Add a new entry (name, URL, description, tag, password)
- **Remove password** — Select and delete a stored entry
- **View passwords** — List all stored passwords (filtered by name or tag)
- **Exit** — Quit securely

---

## 📁 Where is my data stored?

Your passwords are stored securely in:

- `pwdb.encrypted` — binary-encrypted SQLite dump
- `settings.json` — stores bcrypt hash + salt (not the actual password!)

Nothing is stored in plaintext. Everything else is kept in-memory.

---

## 🧪 Example

```
$ python pwdb.py

           ..  
._ .    , _||_ 
[_) \/\/ (_][_)
|    

github.com/mariosasodotcom/pwdb

=== Initial Setup: Create a Master Password ===
Enter new master password: ********
Re-enter to confirm: ********

Setup complete. Encrypted database created.

Select an action:
> Add password
  View passwords
  Exit
```

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0**.

See [`LICENSE`](./LICENSE) for more information.

```
Copyright (C) 2025 mariosasodotcom

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
```

---

## 🙋‍♂️ Author

Made with care by [mariosasodotcom](https://github.com/mariosasodotcom)

Contributions, feedback and forks are welcome!
