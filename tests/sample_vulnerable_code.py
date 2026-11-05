import os
import subprocess
import requests

# 1. Hardcoded secret credential
api_key = "sk_live_93847291837492817293"

def run_user_cmd(cmd_str):
    # 2. Command injection via shell=True
    return subprocess.run(cmd_str, shell=True, capture_output=True)

def fetch_data(url):
    # 3. Disabled SSL verification
    response = requests.get(url, verify=False)
    return response.json()

def query_user_profile(cursor, username):
    # 4. SQL Injection via string interpolation
    query = f"SELECT id, email, role FROM users WHERE username = '{username}'"
    return cursor.execute(query)

def process_file_data(filename):
    # 5. Swallowed exception & 6. Unclosed file
    try:
        f = open(filename, "r")
        return f.read()
    except:
        pass
