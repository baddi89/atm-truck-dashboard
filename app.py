import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

st.set_page_config(page_title="ATM TRUCK", page_icon="🚛", layout="wide")

# Firebase connection
if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["firebase_key"])
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.title("🚛 ATM TRUCK Dashboard")

docs = db.collection("requests").stream()

for doc in docs:
    data = doc.to_dict()
    st.write(data)
