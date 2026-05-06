import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
import pandas as pd

st.set_page_config(
    page_title="ATM TRUCK Admin",
    page_icon="🚛",
    layout="wide"
)

# Firebase
if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["firebase_key"])
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# CSS
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: #0f172a;
}
[data-testid="stSidebar"] * {
    color: white;
}
.main-title {
    font-size: 38px;
    font-weight: 900;
    color: #0f172a;
}
.page-subtitle {
    font-size: 17px;
    color: #64748b;
    margin-bottom: 25px;
}
.kpi-card {
    padding: 22px;
    border-radius: 20px;
    background: white;
    border: 1px solid #e5e7eb;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}
.kpi-label {
    color: #64748b;
    font-size: 15px;
}
.kpi-value {
    font-size: 34px;
    font-weight: 900;
    color: #0f172a;
}
.order-card {
    padding: 22px;
    border-radius: 20px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    margin-bottom: 18px;
}
.badge {
    padding: 7px 15px;
    border-radius: 999px;
    font-weight: 800;
    display: inline-block;
}
.pending {background:#fff7ed;color:#c2410c;}
.accepted {background:#ecfdf5;color:#047857;}
.rejected {background:#fef2f2;color:#b91c1c;}
.new {background:#eff6ff;color:#1d4ed8;}
</style>
""", unsafe_allow_html=True)


def get_requests():
    docs = list(db.collection("requests").stream())
    data = []
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        data.append(item)
    return data


def update_request(doc_id, payload):
    payload["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.collection("requests").document(doc_id).update(payload)


def status_badge(status):
    status = status or "pending"
    if status == "accepted":
        return '<span class="badge accepted">✅ مقبول</span>'
    if status == "rejected":
        return '<span class="badge rejected">❌ مرفوض</span>'
    if status == "new":
        return '<span class="badge new">🆕 جديد</span>'
    return '<span class="badge pending">⏳ في الانتظار</span>'


# Sidebar
with st.sidebar:
    st.markdown("## 🚛 ATM TRUCK")
    st.markdown("لوحة الإدارة")
    page = st.radio(
        "القائمة",
        ["Dashboard", "Orders", "Drivers", "Trucks", "Analytics", "Export"]
    )

requests = get_requests()

total = len(requests)
pending = len([r for r in requests if r.get("status", "pending") == "pending"])
accepted = len([r for r in requests if r.get("status") == "accepted"])
rejected = len([r for r in requests if r.get("status") == "rejected"])

# DASHBOARD
if page == "Dashboard":
    st.markdown('<div class="main-title">🚛 ATM TRUCK Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">نظرة عامة على الطلبات والشاحنات</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">إجمالي الطلبات</div>
            <div class="kpi-value">{total}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">في الانتظار</div>
            <div class="kpi-value">{pending}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">مقبولة</div>
            <div class="kpi-value">{accepted}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">مرفوضة</div>
            <div class="kpi-value">{rejected}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 الطلبات حسب الحالة")
        chart_df = pd.DataFrame({
            "الحالة": ["pending", "accepted", "rejected"],
            "العدد": [pending, accepted, rejected]
        })
        st.bar_chart(chart_df.set_index("الحالة"))

    with col2:
        st.subheader("🕘 آخر الطلبات")
        latest = list(reversed(requests))[:5]
        if latest:
            for r in latest:
                st.write(f"**{r.get('name','غير محدد')}** → {r.get('destination','غير محدد')} | {r.get('status','pending')}")
        else:
            st.info("ما كاين حتى طلب.")


# ORDERS
elif page == "Orders":
    st.markdown('<div class="main-title">📦 إدارة الطلبات</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">قبول، رفض، تعديل معلومات الشاحنة والشوفور</div>', unsafe_allow_html=True)

    f1, f2, f3 = st.columns([1, 2, 1])

    with f1:
        status_filter = st.selectbox("فلترة الحالة", ["all", "pending", "accepted", "rejected"])

    with f2:
        search = st.text_input("🔍 بحث بالاسم، الهاتف، الانطلاق، الوجهة، الحمولة")

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

    st.markdown("---")

    if not filtered:
        st.warning("ما كاين حتى طلب مطابق.")
    else:
        for req in filtered:
            doc_id = req["id"]
            status = req.get("status", "pending")

            st.markdown('<div class="order-card">', unsafe_allow_html=True)

            top1, top2 = st.columns([4, 1])
            with top1:
                st.markdown(f"### طلب رقم `{doc_id}`")
            with top2:
                st.markdown(status_badge(status), unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)

            with c1:
                st.write("👤 **الزبون / العامل:**", req.get("name", "غير محدد"))
                st.write("📞 **الهاتف:**", req.get("phone", "غير محدد"))
                st.write("📍 **الانطلاق:**", req.get("start_location", "غير محدد"))

            with c2:
                st.write("🎯 **الوجهة:**", req.get("destination", "غير محدد"))
                st.write("📦 **نوع الحمولة:**", req.get("cargo_type", "غير محدد"))
                st.write("⚖️ **الوزن:**", req.get("weight", "غير محدد"))

            with c3:
                st.write("🚛 **الشاحنة:**", req.get("truck_info", "غير محدد"))
                st.write("📞 **الشوفور:**", req.get("driver_phone", "غير محدد"))
                st.write("⏱️ **وقت الوصول:**", req.get("arrival_time", "غير محدد"))

            st.info("📝 ملاحظات: " + str(req.get("notes", "لا توجد")))
            st.write("🧾 **ملاحظة المسؤول:**", req.get("admin_note", "لا توجد"))

            with st.expander("✏️ معالجة الطلب"):
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
                    if st.button("✅ قبول الطلب", key=f"accept_{doc_id}"):
                        update_request(doc_id, {
                            "status": "accepted",
                            "driver_phone": driver_phone,
                            "truck_info": truck_info,
                            "arrival_time": arrival_time,
                            "admin_note": admin_note
                        })
                        st.success("تم قبول الطلب")
                        st.rerun()

                with b2:
                    if st.button("⏳ قيد الانتظار", key=f"pending_{doc_id}"):
                        update_request(doc_id, {
                            "status": "pending",
                            "admin_note": admin_note
                        })
                        st.info("تم إرجاع الطلب للانتظار")
                        st.rerun()

                with b3:
                    if st.button("❌ رفض الطلب", key=f"reject_{doc_id}"):
                        update_request(doc_id, {
                            "status": "rejected",
                            "admin_note": admin_note
                        })
                        st.error("تم رفض الطلب")
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)


# DRIVERS
elif page == "Drivers":
    st.markdown('<div class="main-title">👨‍✈️ Drivers</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">إدارة الشوفورات لاحقًا</div>', unsafe_allow_html=True)

    st.info("هنا نزيدولك من بعد: إضافة شوفور، رقم الهاتف، الحالة، الطلبات المخصصة ليه.")


# TRUCKS
elif page == "Trucks":
    st.markdown('<div class="main-title">🚚 Trucks</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">إدارة الشاحنات لاحقًا</div>', unsafe_allow_html=True)

    st.info("هنا نزيدولك من بعد: نوع الشاحنة، matricule، الحمولة، الحالة، الصيانة.")


# ANALYTICS
elif page == "Analytics":
    st.markdown('<div class="main-title">📈 Analytics</div>', unsafe_allow_html=True)

    if not requests:
        st.warning("ما كاينش بيانات باش نعرض analytics.")
    else:
        df = pd.DataFrame(requests)

        if "cargo_type" in df.columns:
            st.subheader("📦 أكثر أنواع الحمولة")
            st.bar_chart(df["cargo_type"].value_counts())

        if "destination" in df.columns:
            st.subheader("🎯 أكثر الوجهات")
            st.bar_chart(df["destination"].value_counts())


# EXPORT
elif page == "Export":
    st.markdown('<div class="main-title">⬇️ Export</div>', unsafe_allow_html=True)

    if requests:
        df = pd.DataFrame(requests)
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "تحميل كل الطلبات CSV",
            data=csv,
            file_name="atm_truck_requests.csv",
            mime="text/csv"
        )
    else:
        st.info("ما كاين حتى طلب للتصدير.")
