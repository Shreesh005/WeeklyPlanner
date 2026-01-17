import os
import sys
import streamlit as st
from supabase import create_client, Client
import pandas as pd

# ------------------ PYTHON VERSION GUARD ------------------
if sys.version_info[:2] < (3, 11):
    raise RuntimeError("Python 3.11+ required")

# ------------------ ENV VARIABLES (RENDER SAFE) ------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase credentials not found. Set SUPABASE_URL and SUPABASE_KEY in environment variables.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------ CONSTANTS ------------------
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DEFAULT_CELL = {"text": "", "bg": "#1e1e1e", "fg": "#ffffff"}

# ------------------ DB HELPERS ------------------
def load_schedule():
    res = supabase.table("schedules").select("data").eq("name", "default").execute()
    if res.data:
        return res.data[0]["data"]
    return {}

def save_schedule(data):
    supabase.table("schedules").upsert(
        {"name": "default", "data": data},
        on_conflict="name"
    ).execute()

# ------------------ SESSION STATE INIT ------------------
if "data" not in st.session_state:
    st.session_state.data = load_schedule()

if "slots" not in st.session_state:
    st.session_state.slots = list(st.session_state.data.keys())
    if not st.session_state.slots:
        st.session_state.slots = ["Slot 1"]
        st.session_state.data["Slot 1"] = {d: DEFAULT_CELL.copy() for d in WEEKDAYS}
        save_schedule(st.session_state.data)

# ------------------ SIDEBAR ------------------
page = st.sidebar.radio("Navigate", ["View", "Edit"])

# =========================================================
# ======================== VIEW ===========================
# =========================================================
if page == "View":
    st.title("Weekly Planner")

    html = """
    <style>
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #333; padding: 10px; text-align: center; }
    th { background: #111; color: white; }
    </style>
    <table>
    <tr>
        <th>Time</th>
    """

    for day in WEEKDAYS:
        html += f"<th>{day}</th>"
    html += "</tr>"

    for slot in st.session_state.slots:
        html += f"<tr><th>{slot}</th>"
        for day in WEEKDAYS:
            cell = st.session_state.data[slot][day]
            html += (
                f"<td style='background:{cell['bg']};"
                f"color:{cell['fg']};"
                f"font-weight:bold;'>"
                f"{cell['text']}</td>"
            )
        html += "</tr>"

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

    if st.button("Export CSV"):
        df = pd.DataFrame(
            {day: [st.session_state.data[s][day]["text"] for s in st.session_state.slots]
             for day in WEEKDAYS},
            index=st.session_state.slots
        )
        st.download_button(
            "Download CSV",
            df.to_csv().encode(),
            "weekly_planner.csv",
            "text/csv"
        )

# =========================================================
# ======================== EDIT ===========================
# =========================================================
else:
    st.title("Edit Weekly Planner")

    # -------- ADD SLOT --------
    new_slot = st.text_input("Add new slot")
    if st.button("Add Slot"):
        if not new_slot.strip():
            st.warning("Slot name cannot be empty")
        elif new_slot in st.session_state.slots:
            st.warning("Slot already exists")
        else:
            st.session_state.slots.append(new_slot)
            st.session_state.data[new_slot] = {d: DEFAULT_CELL.copy() for d in WEEKDAYS}
            save_schedule(st.session_state.data)
            st.experimental_rerun()

    # -------- DELETE SLOT --------
    del_slot = st.selectbox("Delete slot", [""] + st.session_state.slots)
    if del_slot and st.button("Delete Selected Slot"):
        st.session_state.slots.remove(del_slot)
        st.session_state.data.pop(del_slot)
        save_schedule(st.session_state.data)
        st.experimental_rerun()

    st.divider()

    # -------- EDIT SLOTS --------
    for i, slot in enumerate(list(st.session_state.slots)):
        st.subheader(f"Slot {i+1}")

        new_name = st.text_input("Slot name", slot, key=f"name_{i}")
        if new_name != slot and new_name.strip():
            if new_name in st.session_state.data:
                st.warning("Duplicate slot name")
            else:
                st.session_state.slots[i] = new_name
                st.session_state.data[new_name] = st.session_state.data.pop(slot)
                save_schedule(st.session_state.data)
                st.experimental_rerun()

        cols = st.columns(len(WEEKDAYS))
        for j, day in enumerate(WEEKDAYS):
            cell = st.session_state.data[st.session_state.slots[i]][day]
            with cols[j]:
                cell["text"] = st.text_area(day, cell["text"], key=f"{i}-{day}-text")
                cell["bg"] = st.color_picker("BG", cell["bg"], key=f"{i}-{day}-bg")
                cell["fg"] = st.color_picker("Text", cell["fg"], key=f"{i}-{day}-fg")

    if st.button("Save All Changes"):
        save_schedule(st.session_state.data)
        st.success("Saved successfully")
