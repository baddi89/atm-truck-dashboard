import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

st.set_page_config(page_title="ATM TRUCK", page_icon="🚛", layout="wide")

if not firebase_admin._apps:
    cred = credentials.Certificate("key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.markdown("""
<style>
.main-title {
    font-size: 38px;
    font-weight: bold;
    color: #1f2937;
}
.card {
    padding: 18px;
    border-radius: 14px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    margin-bottom: 18px;
}
.status-accepted {color: green; font-weight: bold;}
.status-pending {color: orange; font-weight: bold;}
.status-rejected {color: red; font-weight: bold;}
.small-text {color: #6b7280;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🚛 ATM TRUCK Dashboard</div>', unsafe_allow_html=True)
st.write("لوحة تحكم متطورة لطلبات الشاحنات")

docs = list(db.collection("requests").stream())
requests = []

for doc in docs:
    data = doc.to_dict()
    data["id"] = doc.id
    requests.append(data)

total = len(requests)
accepted = len([r for r in requests if r.get("status") == "accepted"])
pending = len([r for r in requests if r.get("status", "pending") == "pending"])
rejected = len([r for r in requests if r.get("status") == "rejected"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("📦 كامل الطلبات", total)
c2.metric("⏳ في الانتظار", pending)
c3.metric("✅ مقبولة", accepted)
c4.metric("❌ مرفوضة", rejected)

st.markdown("---")

left, right = st.columns([1, 2])

with left:
    st.subheader("🔎 الفلاتر")
    status_filter = st.selectbox(
        "الحالة",
        ["all", "pending", "accepted", "rejected"]
    )

with right:
    st.subheader("🔍 البحث")
    search = st.text_input("ابحث بالاسم، الهاتف، الوجهة، أو مكان الانطلاق")

filtered = requests

if status_filter != "all":
    filtered = [r for r in filtered if r.get("status", "pending") == status_filter]

if search.strip():
    s = search.lower()
    filtered = [
        r for r in filtered
        if s in str(r.get("name", "")).lower()
        or s in str(r.get("phone", "")).lower()
        or s in str(r.get("destination", "")).lower()
        or s in str(r.get("start_location", "")).lower()
    ]

st.markdown("---")
st.subheader("📋 قائمة الطلبات")

if not filtered:
    st.warning("ما كاين حتى طلب مطابق للبحث.")
else:
    for req in filtered:
        doc_id = req["id"]
        status = req.get("status", "pending")

        if status == "accepted":
            status_html = '<span class="status-accepted">✅ مقبول</span>'
        elif status == "rejected":
            status_html = '<span class="status-rejected">❌ مرفوض</span>'
        else:
            status_html = '<span class="status-pending">⏳ في الانتظار</span>'

        st.markdown('<div class="card">', unsafe_allow_html=True)

        top1, top2 = st.columns([3, 1])
        with top1:
            st.markdown(f"### طلب: `{doc_id}`")
        with top2:
            st.markdown(status_html, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("👤 **العامل:**", req.get("name", "غير محدد"))
            st.write("📞 **الهاتف:**", req.get("phone", "غير محدد"))
            st.write("📍 **الانطلاق:**", req.get("start_location", "غير محدد"))

        with col2:
            st.write("🎯 **الوجهة:**", req.get("destination", "غير محدد"))
            st.write("📦 **الحمولة:**", req.get("cargo_type", "غير محدد"))
            st.write("⚖️ **الوزن:**", req.get("weight", "غير محدد"))

        with col3:
            st.write("🚛 **الشاحنة:**", req.get("truck_info", "غير محدد"))
            st.write("📞 **هاتف الشوفور:**", req.get("driver_phone", "غير محدد"))
            st.write("⏱️ **وقت الوصول:**", req.get("arrival_time", "غير محدد"))

        st.write("📝 **ملاحظات:**", req.get("notes", "لا توجد"))

        with st.expander("✏️ الرد على الطلب / تعديل الحالة"):
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
                "وقت وصول الشاحنة",
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
                if st.button("✅ قبول الطلب", key=f"accept_{doc_id}"):
                    db.collection("requests").document(doc_id).update({
                        "status": "accepted",
                        "driver_phone": driver_phone,
                        "truck_info": truck_info,
                        "arrival_time": arrival_time,
                        "admin_note": admin_note,
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    st.success("تم قبول الطلب")
                    st.rerun()

            with b2:
                if st.button("⏳ إرجاع للانتظار", key=f"pending_{doc_id}"):
                    db.collection("requests").document(doc_id).update({
                        "status": "pending",
                        "admin_note": admin_note,
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    st.info("تم إرجاع الطلب للانتظار")
                    st.rerun()

            with b3:
                if st.button("❌ رفض الطلب", key=f"reject_{doc_id}"):
                    db.collection("requests").document(doc_id).update({
                        "status": "rejected",
                        "admin_note": admin_note,
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    st.error("تم رفض الطلب")
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)