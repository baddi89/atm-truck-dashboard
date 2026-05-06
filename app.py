import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
import pandas as pd

st.set_page_config(page_title="ATM TRUCK", page_icon="🚛", layout="wide")

if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["firebase_key"])
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.markdown("""
<style>
.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #0f172a;
}
.subtitle {
    color: #64748b;
    font-size: 18px;
}
.card {
    padding: 20px;
    border-radius: 18px;
    background: linear-gradient(135deg, #ffffff, #f8fafc);
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    margin-bottom: 18px;
}
.badge {
    padding: 6px 14px;
    border-radius: 999px;
    font-weight: 700;
    display: inline-block;
}
.pending {background:#fff7ed;color:#c2410c;}
.accepted {background:#ecfdf5;color:#047857;}
.rejected {background:#fef2f2;color:#b91c1c;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🚛 ATM TRUCK</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">لوحة تحكم ذكية لإدارة طلبات الشاحنات</div>', unsafe_allow_html=True)

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

st.markdown("---")

m1, m2, m3, m4 = st.columns(4)
m1.metric("📦 إجمالي الطلبات", total)
m2.metric("⏳ في الانتظار", pending)
m3.metric("✅ مقبولة", accepted)
m4.metric("❌ مرفوضة", rejected)

st.markdown("---")

f1, f2, f3 = st.columns([1, 2, 1])

with f1:
    status_filter = st.selectbox("فلترة الحالة", ["all", "pending", "accepted", "rejected"])

with f2:
    search = st.text_input("🔍 بحث بالاسم، الهاتف، الانطلاق، الوجهة")

with f3:
    sort_mode = st.selectbox("ترتيب", ["الأحدث", "الأقدم"])

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
        or s in str(r.get("cargo_type", "")).lower()
    ]

if sort_mode == "الأحدث":
    filtered = list(reversed(filtered))

if requests:
    df = pd.DataFrame(requests)
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ تحميل كل الطلبات CSV",
        data=csv,
        file_name="atm_truck_requests.csv",
        mime="text/csv"
    )

st.subheader("📋 الطلبات")

if not filtered:
    st.warning("ما كاين حتى طلب مطابق.")
else:
    for req in filtered:
        doc_id = req["id"]
        status = req.get("status", "pending")

        if status == "accepted":
            badge = '<span class="badge accepted">✅ مقبول</span>'
        elif status == "rejected":
            badge = '<span class="badge rejected">❌ مرفوض</span>'
        else:
            badge = '<span class="badge pending">⏳ في الانتظار</span>'

        st.markdown('<div class="card">', unsafe_allow_html=True)

        top1, top2 = st.columns([3, 1])
        with top1:
            st.markdown(f"### طلب رقم `{doc_id}`")
        with top2:
            st.markdown(badge, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)

        with c1:
            st.write("👤 **العامل:**", req.get("name", "غير محدد"))
            st.write("📞 **هاتف العامل:**", req.get("phone", "غير محدد"))
            st.write("📍 **مكان الانطلاق:**", req.get("start_location", "غير محدد"))

        with c2:
            st.write("🎯 **الوجهة:**", req.get("destination", "غير محدد"))
            st.write("📦 **نوع الحمولة:**", req.get("cargo_type", "غير محدد"))
            st.write("⚖️ **الوزن:**", req.get("weight", "غير محدد"))

        with c3:
            st.write("🚛 **الشاحنة:**", req.get("truck_info", "غير محدد"))
            st.write("📞 **الشوفور:**", req.get("driver_phone", "غير محدد"))
            st.write("⏱️ **وقت الوصول:**", req.get("arrival_time", "غير محدد"))

        st.info("📝 ملاحظات العامل: " + str(req.get("notes", "لا توجد")))
        st.write("🧾 **ملاحظة المسؤول:**", req.get("admin_note", "لا توجد"))

        with st.expander("✏️ معالجة الطلب"):
            driver_phone = st.text_input("رقم هاتف الشوفور", value=req.get("driver_phone", ""), key=f"driver_{doc_id}")
            truck_info = st.text_input("معلومات الشاحنة", value=req.get("truck_info", ""), key=f"truck_{doc_id}")
            arrival_time = st.text_input("وقت الوصول", value=req.get("arrival_time", ""), key=f"time_{doc_id}")
            admin_note = st.text_area("ملاحظة المسؤول", value=req.get("admin_note", ""), key=f"note_{doc_id}")

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
                if st.button("⏳ قيد الانتظار", key=f"pending_{doc_id}"):
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
