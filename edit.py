import streamlit as st
import sqlite3

def create_connection():
    conn = sqlite3.connect('db_moris.db')
    return conn

def get_user_data(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM user WHERE username = ? AND password = ?"
    cursor.execute(query, (username, password))
    result = cursor.fetchone()
    conn.close()
    return result

def update_user_data(user_id, new_username, new_email, new_password):
    conn = create_connection()
    cursor = conn.cursor()
    query = "UPDATE user SET username = ?, email = ?, password = ? WHERE id = ?"
    cursor.execute(query, (new_username, new_email, new_password, user_id))
    conn.commit()
    conn.close()

def show_dialog(user_data):
    user_id, email, username, password = user_data
    st.session_state['edit_username'] = username
    st.session_state['edit_email'] = email
    st.session_state['edit_password'] = password

    @st.experimental_dialog("Edit User Data")
    def dialog():
        st.write("Edit Data Anda Di Bawah Ini:")
        new_email = st.text_input("New Email", value=st.session_state['edit_email'])
        new_username = st.text_input("New Username", value=st.session_state['edit_username'], disabled=True)
        new_password = st.text_input("New Password", value=st.session_state['edit_password'], type="password")
        
        if st.button("Save"):
            if not new_email or not new_username or not new_password:
                st.error("Tolong masukkan email, username, dan password terlebih dahulu")
            elif "@gmail.com" not in new_email:
                st.error("Email harus mengandung '@gmail.com'.")
            else:
                update_user_data(user_id, new_username, new_email, new_password)
                st.success("Edit Data Berhasil")
                st.experimental_rerun()
    dialog()

def run():
    st.title("Edit User Data")

    # Tambahkan tombol Logout
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.experimental_rerun()

    if 'logged_in' in st.session_state and st.session_state['logged_in']:
        if 'username' not in st.session_state:
            st.error("Data pengguna tidak di temukan")
            return

        username = st.text_input("Username", value=st.session_state['username'], disabled=True)
        password = st.text_input("Password", value=st.session_state['password'], disabled=True, type="password")

        if st.button("Edit Data"):
            user_data = get_user_data(username, st.session_state['password'])
            if user_data:
                show_dialog(user_data)
            else:
                st.error("Edit data gagal")
    else:
        st.error("Anda harus login terlebih dahulu")

if __name__ == "__main__":
    run()