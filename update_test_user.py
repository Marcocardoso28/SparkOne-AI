import sqlite3

conn = sqlite3.connect('sparkone.db')
cursor = conn.cursor()

# Update existing user or create new one
cursor.execute('''
UPDATE users 
SET username = 'valid_user', password_hash = 'valid_password'
WHERE username = 'testuser'
''')

# If no rows were updated, insert a new user
if cursor.rowcount == 0:
    cursor.execute('''
    INSERT INTO users (email, password_hash, is_active, is_verified, username)
    VALUES ('valid@example.com', 'valid_password', 1, 1, 'valid_user')
    ''')

conn.commit()
conn.close()
print('Test user updated successfully')

