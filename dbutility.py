import pickle
import sqlite3
from web3 import Web3
from passlib.hash import sha256_crypt


endpoint = endpoint = 'HTTP://127.0.0.1:7545'
web3 = Web3(Web3.HTTPProvider(endpoint))

admin_privatekey = '433f1e6d8b1e8df41a3020d692f01c62f20032723c982d8f5363869163b356e7'
password = 'Admin@123'

def create_connection():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    return c, conn

def create_table():
    c, _ = create_connection()
    user_query = '''CREATE TABLE user(
        id integer PRIMARY KEY AUTOINCREMENT,
        email text UNIQUE NOT NULL,
        data blob NOT NULL,
        password text NOT NULL
    )'''
    c.execute(user_query)

def create_admin():
    account = web3.eth.account.encrypt(admin_privatekey,password)
    data = pickle.dumps(account)
    admin_password = sha256_crypt.hash(password)
    c, conn= create_connection()
    c.execute(
        'INSERT INTO user (email,data,password) VALUES( ?, ?, ?)', ('admin@admin.com',data,admin_password))
    conn.commit()

if __name__ == "__main__":
    # create_table()
    create_admin()