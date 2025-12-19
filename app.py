import streamlit as st
import pandas as pd
import json
import os
import random

# --- DATA PERSISTENCE ---
DB_FILE = "players_db.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except:
            return []
    return []

def save_data(players):
    with open(DB_FILE, "w") as f:
        json.dump(players, f)

# --- THEME & STYLING ---
st.set_page_config(page_title="Cricket Team Balancer", layout="wide")

st.markdown("""
<style>
    /* MAIN BACKGROUND */
    .stApp { background-color: #000000; color: #D4AF37; }
    
    /* INPUT FIELDS */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div { 
        background-color: #1a1a1a !important; 
        color: #D4AF37 !important; 
        border: 1px solid #D4AF37 !important; 
    }
    
    /* DROPDOWN MENU TEXT FIX */
    ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #1a1a1a !important;
    }
    li[role="option"] {
        color: #D4AF37 !important;
    }
    
    /* BUTTON STYLING - FORCED BLACK TEXT */
    div.stButton > button { 
        background-color: #D4AF37 !important; 
        color: #000000 !important; 
        font-weight: 900 !important;
        border: none !important;
        width: 100%;
        font-size: 16px !important;
    }
    /* Targeted fix for text inside buttons */
    div.stButton > button p {
        color: #000000 !important;
    }
    div.stButton > button:hover {
        background-color: #F4CF57 !important;
        color: #000000 !important;
    }

    /* HEADERS */
    h1, h2, h3, h4, h5, p, label { color: #D4AF37 !important; }
    
    /* DATA EDITOR STYLING */
    div[data-testid="stDataEditor"] {
        border: 1px solid #D4AF37;
        border-radius: 5px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

if 'players' not in st.session_state:
    st.session_state.players = load_data()

# --- HELPER FUNCTIONS ---
def balance_teams(players):
    best_a, best_b = [], []
    min_overall_diff = float('inf')
    
    # Run 2000 iterations to find the best balance
    for _ in range(2000):
        random.shuffle(players)
        mid = len(players) // 2
        t1, t2 = players[:mid], players[mid:]
        
        # Calculate stats
        t1_bat = sum(p.get('Batting', 0) for p in t1)
        t2_bat = sum(p.get('Batting', 0) for p in t2)
        
        t1_bowl = sum(p.get('Bowling', 0) for p in t1)
        t2_bowl = sum(p.get('Bowling', 0) for p in t2)
        
        # Total power includes Booster weight
        t1_tot = t1_bat + t1_bowl + sum(p.get('Booster', 0) * 2 for p in t1)
        t2_tot = t2_bat + t2_bowl + sum(p.get('Booster', 0) * 2 for p in t2)
        
        # Constraint: Batting & Bowling difference <= 3
        if abs(t1_bat - t2_bat) <= 3 and abs(t1_bowl - t2_bowl) <= 3:
            # Priority: Minimize Overall Points difference
            overall_diff = abs(t1_tot - t2_tot)
            if overall_diff < min_overall_diff:
                min_overall_diff = overall_diff
                best_a, best_b = t1, t2
                
    return best_a, best_b

# --- UI INTERFACE ---
st.title("🏆 CRICKET TEAM BALANCER")

# 1. ADD PLAYER SECTION
with st.expander("➕ Add New Player", expanded=True):
    # Added "Role" Column
    c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
    
    name = c1.text_input("Name")
    role = c2.selectbox("Role", ["All-rounder", "Batsman", "Bowler"]) # Added Role
    bat_rating = c3.number_input("Batting", 0, 10, 5)
    bowl_rating = c4.number_input("Bowling", 0, 10, 5)
    
    # Booster with Tooltip
    boost = c5.number_input("Booster", 0, 10, 0, 
                            help="Extra points for Captains or Key Players.")
    
    if st.button("ADD PLAYER"):
        if name:
            new_player = {
                "Name": name, 
                "Role": role,
                "Batting": bat_rating, 
                "Bowling": bowl_rating, 
                "Booster": boost
            }
            # Remove duplicate names if exists, then add new
            st.session_state.players = [p for p in st.session_state.players if p.get("Name") != name]
            st.session_state.players.append(new_player)
            save_data(st.session_state.players)
            st.rerun()

# 2. EDIT SQUAD SECTION
st.write("---")
st.subheader("📋 Current Squad")

if st.session_state.players:
    df = pd.DataFrame(st.session_state.players)
    
    # Ensure all columns exist
    for col in ['Role', 'Batting', 'Bowling', 'Booster']:
        if col not in df.columns:
            df[col] = 0 if col != 'Role' else 'All-rounder'
            
    # Filter columns for display
    df_display = df[['Name', 'Role', 'Batting', 'Bowling', 'Booster']]
    
    # Editable Table
    edited_df = st.data_editor(
        df_display, 
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editor",
        column_config={
            "Role": st.column_config.SelectboxColumn(
                "Role",
                options=["All-rounder", "Batsman", "Bowler"],
                required=True
            )
        }
    )
    
    # Save Logic
    current_data = edited_df.to_dict('records')
    if len(current_data) != len(st.session_state.players) or current_data != [
        {k: p.get(k, 0 if k!='Role' else '') for k in ['Name', 'Role', 'Batting', 'Bowling', 'Booster']} 
        for p in st.session_state.players
    ]:
        st.session_state.players = current_data
        save_data(st.session_state.players)

# 3. GENERATE TEAMS
st.write("---")
if len(st.session_state.players) >= 2:
    # Button is labeled clearly to show it can regenerate
    if st.button("⚡ GENERATE / RE-ROLL TEAMS"):
        t1, t2 = balance_teams(st.session_state.players)
        
        if t1:
            col_a, col_b = st.columns(2)
            
            def get_stats(team):
                bat = sum(p.get('Batting', 0) for p in team)
                bowl = sum(p.get('Bowling', 0) for p in team)
                tot = bat + bowl + sum(p.get('Booster', 0)*2 for p in team)
                return bat, bowl, tot

            a_bat, a_bowl, a_tot = get_stats(t1)
            b_bat, b_bowl, b_tot = get_stats(t2)

            # Added 'Role' and 'Booster' to the final view
            cols_to_show = ['Name', 'Role', 'Batting', 'Bowling', 'Booster']

            with col_a:
                st.markdown("### 🟡 TEAM GOLD")
                st.dataframe(pd.DataFrame(t1)[cols_to_show], use_container_width=True, hide_index=True)
                st.success(f"🏏 Bat: {a_bat} | 🥎 Bowl: {a_bowl} | 💪 Total: {a_tot}")

            with col_b:
                st.markdown("### ⚫ TEAM BLACK")
                st.dataframe(pd.DataFrame(t2)[cols_to_show], use_container_width=True, hide_index=True)
                st.warning(f"🏏 Bat: {b_bat} | 🥎 Bowl: {b_bowl} | 💪 Total: {b_tot}")
        else:
            st.error("⚠️ Could not find a perfect balance (Diff < 3). Try adjusting player ratings.")
