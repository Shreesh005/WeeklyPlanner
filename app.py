import os
import sys
import streamlit as st
from supabase import create_client
import pandas as pd

# ------------------ PYTHON CHECK ------------------
if sys.version_info < (3, 11):
    raise RuntimeError("Python 3.11+ required")

# ------------------ ENV ------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("SUPABASE_URL or SUPABASE_KEY missing")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------ CONSTANTS ------------------
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DEFAULT_CELL = {"text": "", "bg": "#1e1e1e", "fg": "#ffffff"}

# ------------------ DB ------------------
def load_schedule():
    res = supabase.table("schedules").select("data").eq("name", "default").execute()
    return res.data[0]["data"] if res.data else {}

def save_schedule(data):
    supabase.table("schedules").upsert(
        {"name": "default", "data": data},
        on_conflict="name"
    ).execute()

# ------------------ STATE INIT ------------------
if "data" not in st.session_state:
    st.session_state.data = load_schedule()

if "slots" not in st.session_state:
    st.session_state.slots = list(st.session_state.data.keys())
    if not st.session_state.slots:
        st.session_state.slots = ["Slot 1"]
        st.session_state.data["Slot 1"] = {d: DEFAULT_CELL.copy() for d in WEEKDAYS}
        save_schedule(st.session_state.data)

# ------------------ NAV ------------------
page = st.sidebar.radio("Navigate", ["View", "Edit"])

# ==================================================
# ===================== VIEW =======================
# ==================================================
if page == "View":
    st.title("Weekly Planner")

    html = """
    <style>
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #333; padding: 10px; text-align: center; }
    th { background: #111; color: white; }
    </style>
    <table>
    <tr><th>Slot</th>
    """

    for d in WEEKDAYS:
        html += f"<th>{d}</th>"
    html += "</tr>"

    for slot in st.session_state.slots:
        html += f"<tr><th>{slot}</th>"
        for d in WEEKDAYS:
            c = st.session_state.data[slot][d]
            html += f"<td style='background:{c['bg']};color:{c['fg']};font-weight:bold'>{c['text']}</td>"
        html += "</tr>"

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

    if st.button("Export CSV"):
        df = pd.DataFrame(
            {d: [st.session_state.data[s][d]["text"] for s in st.session_state.slots] for d in WEEKDAYS},
            index=st.session_state.slots
        )
        st.download_button("Download", df.to_csv().encode(), "weekly.csv")

# ==================================================
# ===================== EDIT =======================
# ==================================================
else:
    st.title("Edit Planner")

    # -------- ADD SLOT --------
    new_slot = st.text_input("New slot name")
    if st.button("Add Slot"):
        if new_slot and new_slot not in st.session_state.slots:
            st.session_state.slots.append(new_slot)
            st.session_state.data[new_slot] = {d: DEFAULT_CELL.copy() for d in WEEKDAYS}
            save_schedule(st.session_state.data)
            st.rerun()

    st.divider()

    # -------- SLOT EDITING --------
    for i, slot in enumerate(st.session_state.slots.copy()):
        st.subheader(f"Slot {i+1}")

        col1, col2, col3 = st.columns([6,1,1])

        # ---- Rename (POSITION SAFE) ----
        with col1:
            new_name = st.text_input("Slot name", slot, key=f"name_{i}")

        if new_name != slot and new_name.strip():
            if new_name in st.session_state.data:
                st.warning("Duplicate slot name")
            else:
                st.session_state.slots[i] = new_name
                st.session_state.data[new_name] = st.session_state.data.pop(slot)
                save_schedule(st.session_state.data)
                st.rerun()

        # ---- MOVE UP ----
        with col2:
            if i > 0 and st.button("⬆", key=f"up_{i}"):
                st.session_state.slots[i-1], st.session_state.slots[i] = (
                    st.session_state.slots[i],
                    st.session_state.slots[i-1]
                )
                save_schedule(st.session_state.data)
                st.rerun()

        # ---- MOVE DOWN ----
        with col3:
            if i < len(st.session_state.slots)-1 and st.button("⬇", key=f"down_{i}"):
                st.session_state.slots[i+1], st.session_state.slots[i] = (
                    st.session_state.slots[i],
                    st.session_state.slots[i+1]
                )
                save_schedule(st.session_state.data)
                st.rerun()

        cols = st.columns(len(WEEKDAYS))
        for j, d in enumerate(WEEKDAYS):
            cell = st.session_state.data[st.session_state.slots[i]][d]
            with cols[j]:
                cell["text"] = st.text_area(d, cell["text"], key=f"{i}-{d}-text")
                cell["bg"] = st.color_picker("BG", cell["bg"], key=f"{i}-{d}-bg")
                cell["fg"] = st.color_picker("FG", cell["fg"], key=f"{i}-{d}-fg")

    if st.button("Save All"):
        save_schedule(st.session_state.data)
        st.success("Saved")
