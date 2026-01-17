import streamlit as st
from supabase import create_client, Client
import json
import pandas as pd
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase credentials not found! Set SUPABASE_URL and SUPABASE_KEY as environment variables.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------- Supabase Setup -----------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL") or "YOUR_SUPABASE_URL"
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY") or "YOUR_SUPABASE_KEY"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------- Constants -----------------
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ----------------- Version Guard -----------------
import sys
if not (sys.version_info.major == 3 and sys.version_info.minor == 11):
    raise RuntimeError(f"This app requires Python 3.11.x! Current version: {sys.version}")

# ----------------- Helpers -----------------
def save_schedule(data):
    supabase.table("schedules").upsert(
        {"name": "default", "data": data},
        on_conflict="name"
    ).execute()

def load_schedule():
    response = supabase.table("schedules").select("*").eq("name", "default").execute()
    if response.data and len(response.data) > 0:
        return response.data[0]["data"]
    return {}

# ----------------- Initialize Session State -----------------
if "data" not in st.session_state:
    st.session_state.data = load_schedule()
if "slots" not in st.session_state:
    st.session_state.slots = list(st.session_state.data.keys()) or ["Slot 1"]

# ----------------- Sidebar Navigation -----------------
page = st.sidebar.selectbox("Go to", ["View", "Edit"])

# ----------------- View Page -----------------
if page == "View":
    st.title("Weekly Planner - View")
    
    # Build HTML table dynamically
    html = "<table style='border-collapse: collapse; width: 100%;'>"
    html += "<tr><th style='border:1px solid #333;padding:8px;'>Time</th>"
    for day in WEEKDAYS:
        html += f"<th style='border:1px solid #333;padding:8px;'>{day}</th>"
    html += "</tr>"
    
    for slot in st.session_state.slots:
        html += f"<tr><th style='border:1px solid #333;padding:8px;background:#222;color:#fff;'>{slot}</th>"
        for day in WEEKDAYS:
            cell = st.session_state.data.get(slot, {}).get(day, {"text":"", "bg":"#1e1e1e", "fg":"#ffffff"})
            html += f"<td style='border:1px solid #333;padding:8px;background:{cell['bg']};color:{cell['fg']};font-weight:bold;'>{cell['text']}</td>"
        html += "</tr>"
    html += "</table>"
    
    st.markdown(html, unsafe_allow_html=True)
    
    # Optional: export table to CSV/PDF
    if st.button("Export to CSV"):
        export_df = pd.DataFrame({
            day: [st.session_state.data[slot][day]["text"] if day in st.session_state.data[slot] else "" for slot in st.session_state.slots]
            for day in WEEKDAYS
        }, index=st.session_state.slots)
        export_df.to_csv("weekly_plan.csv")
        st.success("CSV saved as weekly_plan.csv")

# ----------------- Edit Page -----------------
else:
    st.title("Weekly Planner - Edit")
    
    # Add new slot
    new_slot = st.text_input("New slot name", "")
    if st.button("Add Slot") and new_slot.strip():
        if new_slot in st.session_state.slots:
            st.warning("Slot already exists!")
        else:
            st.session_state.slots.append(new_slot)
            st.session_state.data[new_slot] = {day: {"text":"", "bg":"#1e1e1e", "fg":"#ffffff"} for day in WEEKDAYS}
            save_schedule(st.session_state.data)
            st.experimental_rerun()
    
    # Delete slot
    slot_to_delete = st.selectbox("Delete slot", [""] + st.session_state.slots)
    if slot_to_delete and st.button("Delete Selected Slot"):
        st.session_state.slots.remove(slot_to_delete)
        st.session_state.data.pop(slot_to_delete, None)
        save_schedule(st.session_state.data)
        st.experimental_rerun()
    
    # Editable slots & cells
    for idx, slot in enumerate(st.session_state.slots):
        st.subheader(f"Slot {idx+1}")
        
        # Editable slot name
        new_slot_name = st.text_input(f"Edit slot name", value=slot, key=f"slot-name-{idx}")
        if new_slot_name != slot and new_slot_name.strip():
            if new_slot_name in st.session_state.data:
                st.warning(f"Slot '{new_slot_name}' already exists!")
            else:
                st.session_state.slots[idx] = new_slot_name
                st.session_state.data[new_slot_name] = st.session_state.data.pop(slot)
                save_schedule(st.session_state.data)
                st.experimental_rerun()
        
        # Editable cells
        cols = st.columns(len(WEEKDAYS))
        for i, day in enumerate(WEEKDAYS):
            cell = st.session_state.data[st.session_state.slots[idx]][day]
            with cols[i]:
                cell["text"] = st.text_area(day, cell["text"], key=f"{slot}-{day}-text")
                cell["bg"] = st.color_picker("BG", cell["bg"], key=f"{slot}-{day}-bg")
                cell["fg"] = st.color_picker("Text", cell["fg"], key=f"{slot}-{day}-fg")
    
    # Save button
    if st.button("Save Schedule"):
        save_schedule(st.session_state.data)
        st.success("Schedule saved successfully!")
