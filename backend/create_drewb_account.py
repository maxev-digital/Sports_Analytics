"""Create DrewB user account"""
import sys
sys.path.insert(0, 'C:\\Users\\nashr\\backend')
from auth import add_user

username = "DrewB"
password = "DrewB"

if add_user(username, password):
    print(f"User '{username}' created successfully!")
    print(f"Username: {username}")
    print(f"Password: {password}")
else:
    print(f"User '{username}' already exists")
