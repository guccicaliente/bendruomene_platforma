import os
import sqlite3
import shutil

def check_db(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check auth_user table
        cursor.execute("SELECT COUNT(*) FROM auth_user")
        user_count = cursor.fetchone()[0]
        
        # Get user details
        cursor.execute("SELECT username, email, is_staff, is_superuser FROM auth_user")
        users = cursor.fetchall()
        
        print(f"\nChecking database: {db_path}")
        print(f"Total users found: {user_count}")
        for user in users:
            print(f"Username: {user[0]}, Email: {user[1]}, Is staff: {user[2]}, Is superuser: {user[3]}")
        
        conn.close()
        return user_count > 0
    except Exception as e:
        print(f"Error checking {db_path}: {str(e)}")
        return False

# Check both databases
print("Checking both database files...")
has_users1 = check_db('db.sqlite3')
has_users2 = check_db('db.sqlite3.backup')

# If one database has users and the other doesn't, restore the one with users
if has_users1 and not has_users2:
    print("\nRestoring from db.sqlite3...")
    shutil.copy2('db.sqlite3', 'db.sqlite3.backup')
elif has_users2 and not has_users1:
    print("\nRestoring from db.sqlite3.backup...")
    shutil.copy2('db.sqlite3.backup', 'db.sqlite3') 