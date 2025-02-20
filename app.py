import pandas as pd
import streamlit as st
import joblib
import nltk
import sqlite3
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from st_aggrid.shared import GridUpdateMode

# Membaca model yang sudah dilatih
logreg_model = joblib.load("model100.pkl")

# Memuat TF-IDF Vectorizer yang sudah di-fit
tfidf_vectorizer = joblib.load("tfidf_vectorizer.pkl")

# Fungsi untuk membersihkan teks
def clean_text(text):
    stop_words = set(stopwords.words('indonesian'))
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    text = text.lower()  # Case folding
    words = word_tokenize(text)  # Tokenizing
    cleaned_words = [word for word in words if word not in stop_words]  # Stopword removal
    stemmed_words = [stemmer.stem(word) for word in cleaned_words]  # Stemming
    return " ".join(stemmed_words)

# Fungsi untuk melakukan klasifikasi teks
def classify_text(input_text):
    # Membersihkan teks input
    cleaned_text = clean_text(input_text)
    # Mengubah teks input menjadi vektor fitur menggunakan TF-IDF
    input_vector = tfidf_vectorizer.transform([cleaned_text])
    # Melakukan Analisis menggunakan model
    predicted_label = logreg_model.predict(input_vector)[0]
    return predicted_label

# Fungsi untuk memasukkan data ke database
def insert_to_db(text, sentiment):
    conn = sqlite3.connect('db_moris.db')
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''INSERT INTO riwayat (text, sentiment, date) VALUES (?, ?, ?)''', (text, sentiment, date))
    conn.commit()
    conn.close()

# Fungsi untuk mengambil data dari database
def fetch_data():
    conn = sqlite3.connect('db_moris.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT rowid AS id, text, sentiment, date FROM riwayat''')
    rows = cursor.fetchall()
    conn.close()
    return rows

# Fungsi untuk mengonversi DataFrame ke Excel
@st.cache_data
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        writer.close()  # Gunakan writer.close() untuk menyimpan file
    processed_data = output.getvalue()
    return processed_data

# Fungsi untuk menjalankan website
def run():
    st.title("Website Analisis Sentimen Moris Indonesia")

    tab1, tab2 = st.tabs(["Analisis Satu Kalimat", "Analisis File"])

    with tab1:
        st.header("Masukkan kalimat untuk analisis sentimen:")
        input_text = st.text_input("Masukkan kalimat")
    
        if 'data' not in st.session_state:
            st.session_state['data'] = fetch_data()

        if st.button("Analisis"):
            if input_text.strip() == "":
                st.error("Tolong masukkan kalimat terlebih dahulu.")
            else:
                result = classify_text(input_text)
                st.write("Hasil Analisis Sentimen:", result)
                insert_to_db(input_text, result)
                st.session_state['data'] = fetch_data()
    
        # Menampilkan data dari database sebagai tabel
        data = st.session_state['data']
        if data:
            df = pd.DataFrame(data, columns=['id', 'text', 'sentiment', 'date'])
            df.rename(columns={'text': 'Text', 'sentiment': 'Human'}, inplace=True)
            
            # Konfigurasi AgGrid
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
            gb.configure_default_column(resizable=True, filterable=True, sortable=True)
            grid_options = gb.build()
            
            # Tampilkan tabel dengan AgGrid
            AgGrid(
                df,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                fit_columns_on_grid_load=True,
                theme="streamlit",
            )

            # Tambahkan tombol unduh
            st.download_button(
                label="Unduh data sebagai Excel",
                data=convert_df_to_excel(df),
                file_name="data_sentimen.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.write("Tidak ada data yang tersedia.")

    with tab2:
        st.header("Unggah file untuk Analisis Sentimen")
        uploaded_file = st.file_uploader("Unggah file Excel", type=["xlsx"], key="file_uploader")

        if uploaded_file is not None:
            # Baca file Excel
            df = pd.read_excel(uploaded_file)
            
            # Periksa apakah kolom 'Text' ada di file yang diunggah
            if 'Text' in df.columns:
                # Inisialisasi TF-IDF Vectorizer dan fit_transform pada data teks
                X = df['Text'].apply(clean_text)
                X_tfidf = tfidf_vectorizer.transform(X)
                
                # Lakukan Analisis
                df['Human'] = logreg_model.predict(X_tfidf)
                
                # Tampilkan Analisis
                st.write(df)
                
                # Buat tombol unduh
                st.download_button(
                    label="Unduh file dengan analisis",
                    data=convert_df_to_excel(df),
                    file_name="Analisis_sentimen.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("File harus memiliki kolom 'Text'.")

if __name__ == "__main__":
    run()