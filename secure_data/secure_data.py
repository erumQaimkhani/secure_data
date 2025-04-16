
import streamlit as st
import hashlib
import os
import json
import time
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode
from hashlib import pbkdf2_hmac

DATA_FILE = 'secure_data.json'
SALT = b"secure_salt_value"
LOCKOUT_DURATION = 60  # seconds

# Initialize session state
if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None
if "failed_attempts" not in st.session_state:
    st.session_state.failed_attempts = 0
if "lockout_time" not in st.session_state:
    st.session_state.lockout_time = 0

# Load data from file
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save data to file
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# Generate key using PBKDF2 and base64 encode it
def generate_key(passkey):
    key = pbkdf2_hmac('sha256', passkey.encode(), SALT, 100000)
    return urlsafe_b64encode(key)

# Hash the password
def hash_password(password):
    return pbkdf2_hmac('sha256', password.encode(), SALT, 100000).hex()

# Encrypt text
def encrypt_text(text, key):
    cipher = Fernet(key)
    return cipher.encrypt(text.encode()).decode()

# Decrypt text
def decrypt_text(encrypted_text, key):
    try:
        cipher = Fernet(key)
        return cipher.decrypt(encrypted_text.encode()).decode()
    except Exception:
        return None

# Load stored user data
stored_data = load_data()

# UI
st.title("🔐 Secure Data Encryption System")
menu = ["Home", "Login", "Register", "Store Data", "Retrieve Data"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Home":
    st.subheader("Welcome to the Secure Data Encryption System")
    st.markdown("This app allows you to securely store and retrieve data using encryption.")

elif choice == "Register":
    st.subheader("Register New User")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if username and password:
            if username in stored_data:
                st.error("Username already exists.")
            else:
                stored_data[username] = {
                    "password": hash_password(password),
                    "data": []
                }
                save_data(stored_data)
                st.success("User registered successfully.")
        else:
            st.error("Please enter a username and password.")

elif choice == "Login":
    st.subheader("Login")
    if time.time() < st.session_state.lockout_time:
        remaining = int(st.session_state.lockout_time - time.time())
        st.warning(f"Too many failed attempts. Try again in {remaining} seconds.")
        st.stop()

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in stored_data and stored_data[username]["password"] == hash_password(password):
            st.session_state.authenticated_user = username
            st.session_state.failed_attempts = 0
            st.success(f"Welcome, {username}!")
        else:
            st.session_state.failed_attempts += 1
            remaining_attempts = 3 - st.session_state.failed_attempts
            if st.session_state.failed_attempts >= 3:
                st.session_state.lockout_time = time.time() + LOCKOUT_DURATION
                st.warning(f"Too many failed attempts. Locked out for {LOCKOUT_DURATION} seconds.")
                st.stop()
            else:
                st.error(f"Invalid credentials. {remaining_attempts} attempt(s) remaining.")

elif choice == "Store Data":
    if not st.session_state.authenticated_user:
        st.warning("Please login first.")
    else:
        st.subheader("Store Encrypted Data")
        data = st.text_area("Enter Data to Encrypt")
        passkey = st.text_input("Enter Passkey", type="password")
        if st.button("Encrypt & Save"):
            if data and passkey:
                key = generate_key(passkey)
                encrypted_data = encrypt_text(data, key)
                stored_data[st.session_state.authenticated_user]["data"].append(encrypted_data)
                save_data(stored_data)
                st.success("✅ Data encrypted and stored successfully.")
            else:
                st.error("Please enter both data and passkey.")

elif choice == "Retrieve Data":
    if not st.session_state.authenticated_user:
        st.warning("Please login first.")
    else:
        st.subheader("Retrieve Your Data")
        user_data = stored_data.get(st.session_state.authenticated_user, {}).get("data", [])

        if not user_data:
            st.info("No data stored yet.")
        else:
            st.write("Encrypted Data Entries:")
            for i, item in enumerate(user_data, 1):
                st.code(f"{i}. {item}", language="text")

            encrypted_input = st.text_area("Enter Encrypted Data")
            passkey = st.text_input("Enter Passkey to Decrypt", type="password")

            if st.button("Decrypt"):
                key = generate_key(passkey)
                result = decrypt_text(encrypted_input, key)
                if result:
                    st.success(f"🔓 Decrypted Data: {result}")
                else:
                    st.error("❌ Incorrect passkey or invalid encrypted text.")
