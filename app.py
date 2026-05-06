import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json

st.set_page_config(page_title="ATM TRUCK", page_icon="🚛", layout="wide")

# Firebase connection
if not firebase_admin._apps:
    try:
        # Online Streamlit Cloud
        key_dict = json.loads(st.secrets["firebase_key"])
        cred = credentials.Certificate(key_dict)
    except Exception:
        # Local computer
        cred = credentials.Certificate("key.json")

    firebase_admin.initialize_app(cred)

db = firestore.client()

st.title("🚛 ATM TRUCK - Dashboard")
st.write("لوحة تحكم طلبات الشاحنات")

docs = list(db.collection("requests").stream())
requests = []

for doc in docs:
    data = doc.to_dict()
    data["id"] = doc.id
    requests.append(data)

total = len(requests)
pending = len([r for r in requests if r.get("status", "pending") == "pending"])
accepted = len([r for r in requests if r.get("status") == "accepted"])
rejected = len([r for r in requests if r.get("status") == "rejected"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("📦 كامل الطلبات", total)
c2.metric("⏳ في الانتظار", pending)
c3.metric("✅ مقبولة", accepted)
c4.metric("❌ مرفوضة", rejected)

st.markdown("---")

col_filter, col_search = st.columns([1, 2])

with col_filter:
    status_filter = st.selectbox(
        "فلترة حسب الحالة",
        ["all", "pending", "accepted", "rejected"]
    )

with col_search:
    search = st.text_input("بحث بالاسم، الهاتف، الانطلاق، أو الوجهة")

filtered = requests

if status_filter != "all":
    filtered = [r for r in filtered if r.get("status", "pending") == status_filter]

if search.strip():
    s = search.lower()
    filtered = [
        r for r in filtered
        if s in str(r.get("name", "")).lower()
        or s in str(r.get("phone", "")).lower()
        or s in str(r.get("start_location", "")).lower()
        or s in str(r.get("destination", "")).lower()
    ]

st.subheader("📋 الطلبات")

if not filtered:
    st.warning("ما كاين حتى طلب.")
else:
    for req in filtered:
        doc_id = req["id"]
        status = req.get("status", "pending")

        st.markdown("---")

        if status == "accepted":
            st.success(f"✅ طلب مقبول - {doc_id}")
        elif status == "rejected":
            st.error(f"❌ طلب مرفوض - {doc_id}")
        else:
            st.warning(f"⏳ طلب في الانتظار - {doc_id}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("👤 الاسم:", req.get("name", "غير محدد"))
            st.write("📞 هاتف العامل:", req.get("phone", "غير محدد"))
            st.write("📍 الانطلاق:", req.get("start_location", "غير محدد"))

        with col2:
            st.write("🎯 الوجهة:", req.get("destination", "غير محدد"))
            st.write("📦 الحمولة:", req.get("cargo_type", "غير محدد"))
            st.write("⚖️ الوزن:", req.get("weight", "غير محدد"))

        with col3:
            st.write("🚛 الشاحنة:", req.get("truck_info", "غير محدد"))
            st.write("📞 الشوفور:", req.get("driver_phone", "غير محدد"))
            st.write("⏱️ وقت الوصول:", req.get("arrival_time", "غير محدد"))

        st.write("📝 ملاحظات العامل:", req.get("notes", "لا توجد"))
        st.write("🧾 ملاحظة المسؤول:", req.get("admin_note", "لا توجد"))

        with st.expander("✏️ الرد على الطلب"):
            driver_phone = st.text_input(
                "رقم هاتف الشوفور",
                value=req.get("driver_phone", ""),
                key=f"driver_{doc_id}"
            )

            truck_info = st.text_input(
                "معلومات الشاحنة",
                value=req.get("truck_info", ""),
                key=f"truck_{doc_id}"
            )

            arrival_time = st.text_input(
                "وقت الوصول",
                value=req.get("arrival_time", ""),
                key=f"time_{doc_id}"
            )

            admin_note = st.text_area(
                "ملاحظة المسؤول",
                value=req.get("admin_note", ""),
                key=f"note_{doc_id}"
            )

            b1, b2, b3 = st.columns(3)

            with b1:
                if st.button("✅ قبول", key=f"accept_{doc_id}"):
                    db.collection("requests").document(doc_id).update({
                        "status": "accepted",
                        "driver_phone": driver_phone,
                        "truck_info": truck_info,
                        "arrival_time": arrival_time,
                        "admin_note": admin_note,
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    st.rerun()

            with b2:
                if st.button("⏳ انتظار", key=f"pending_{doc_id}"):
                    db.collection("requests").document(doc_id).update({
                        "status": "pending",
                        "admin_note": admin_note,
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    st.rerun()

            with b3:
                if st.button("❌ رفض", key=f"reject_{doc_id}"):
                    db.collection("requests").document(doc_id).update({
                        "status": "rejected",
                        "admin_note": admin_note,
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    st.rerun()
