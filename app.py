import os
import streamlit as st
from supabase import create_client

# ---------------- CONFIG ----------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase credentials not found! Set SUPABASE_URL and SUPABASE_KEY.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ---------------- DB HELPERS ----------------
def load_schedule():
    res = supabase.table("schedules").select("data").eq("name", "default").single().execute()
    return res.data["data"] if res.data else {}

def save_schedule(data):
    supabase.table("schedules").upsert(
        {"name": "default", "data": data},
        on_conflict="name"
    ).execute()


# ---------------- INIT STATE ----------------
if "data" not in st.session_state:
    db_data = load_schedule()
    if db_data:
        st.session_state.data = db_data
        st.session_state.slots = list(db_data.keys())
    else:
        # default slot
        st.session_state.slots = ["09:00 - 10:00"]
        st.session_state.data = {
            "09:00 - 10:00": {day: {"text": "", "bg": "#1e1e1e", "fg": "#ffffff"} for day in WEEKDAYS}
        }

# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout="wide", page_title="Weekly Planner")

st.markdown("""
<style>
body { background:#0f1117; color:white; }
table { width:100%; border-collapse:collapse; }
th, td { border:1px solid #333; padding:12px; text-align:center; }
th { background:#111; }
</style>
""", unsafe_allow_html=True)

# ---------------- NAVIGATION ----------------
mode = st.sidebar.radio("Mode", ["Edit Schedule", "View Schedule"])

# ==================== EDIT PAGE =================
if mode == "Edit Schedule":
    st.title("🛠 Edit Schedule")

    # --- Add slot ---
    with st.form("add_slot_form"):
        new_slot = st.text_input("Add Time Slot (e.g., 10:00 - 11:00)")
        if st.form_submit_button("➕ Add Slot"):
            if new_slot and new_slot not in st.session_state.data:
                st.session_state.slots.append(new_slot)
                st.session_state.data[new_slot] = {day: {"text": "", "bg": "#1e1e1e", "fg": "#ffffff"} for day in WEEKDAYS}
                save_schedule(st.session_state.data)
                st.success(f"Slot '{new_slot}' added!")

    # --- Delete slot ---
    del_slot = st.selectbox("Delete Slot", ["None"] + st.session_state.slots)
    if del_slot != "None" and st.button("🗑 Delete Slot"):
        st.session_state.slots.remove(del_slot)
        st.session_state.data.pop(del_slot)
        save_schedule(st.session_state.data)
        st.success(f"Slot '{del_slot}' deleted!")

    st.divider()

    # --- Edit table ---
    for slot in st.session_state.slots:
        st.subheader(slot)
        cols = st.columns(len(WEEKDAYS))
        for i, day in enumerate(WEEKDAYS):
            cell = st.session_state.data[slot][day]
            with cols[i]:
                cell["text"] = st.text_area(day, cell["text"], key=f"{slot}-{day}-text")
                cell["bg"] = st.color_picker("BG", cell["bg"], key=f"{slot}-{day}-bg")
                cell["fg"] = st.color_picker("Text", cell["fg"], key=f"{slot}-{day}-fg")

    if st.button("💾 Save Schedule"):
        save_schedule(st.session_state.data)
        st.success("Saved to Supabase cloud!")

# ==================== VIEW PAGE =================
else:
    st.title("📅 Final Schedule")

    # --- Build HTML table dynamically from JSON ---
    html = "<table><tr><th>Time</th>" + "".join(f"<th>{day}</th>" for day in WEEKDAYS) + "</tr>"
    for slot in st.session_state.slots:
        html += f"<tr><th>{slot}</th>"
        for day in WEEKDAYS:
            c = st.session_state.data[slot][day]
            html += f'<td style="background:{c["bg"]};color:{c["fg"]};font-weight:bold;">{c["text"]}</td>'
        html += "</tr>"
    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)
    st.markdown("### 📄 Export")
    st.markdown("Use **Ctrl + P → Save as PDF** (dark mode preserved)")
