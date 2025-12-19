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
                # Ensure we only keep valid lists
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
    .stTextInput input, .stNumberInput input { 
        background-color: #1a1a1a !important; 
        color: #D4AF37 !important; 
        border: 1px solid #D4AF37 !important; 
    }
    
    /* BUTTON STYLING - Fix for invisible text */
    .stButton > button { 
        background-color: #D4AF37 !important; 
        color: #000000 !important; 
        font-weight: 900 !important; /* Extra bold */
        border: none !important;
        width: 100%;
        font-size: 16px !important;
    }
    .stButton > button:hover {
        background-color: #F4CF57 !important; /* Lighter gold on hover */
        color: #000000 !important;
    }

    /* HEADERS */
    h1, h2, h3, h4, h5, p, label { color: #D4AF37 !important; }
    
    /* TABLE / DATA EDITOR STYLING */
    /* Force the data editor to blend in */
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
        
        # Calculate stats safely (handle missing keys if old data exists)
        t1_bat = sum(p.get('Batting', 0) for p in t1)
        t2_bat = sum(p.get('Batting', 0) for p in t2)
        
        t1_bowl = sum(p.get('Bowling', 0) for p in t1)
        t2_bowl = sum(p.get('Bowling', 0) for p in t2)
        
        # Total power includes Booster weight
        t1_tot = t1_bat + t1_bowl + sum(p.get('Booster', 0) * 2 for p in t1)
        t2_tot = t2_bat + t2_bowl + sum(p.get('Booster', 0) * 2 for p in t2)
        
        # Constraint: Batting & Bowling difference <= 3
        if abs(t1_bat - t2_bat) <= 3 and abs(t1_bowl - t2_bowl) <= 3:
            overall_diff = abs(t1_tot - t2_tot)
            if overall_diff < min_overall_diff:
                min_overall_diff = overall_diff
                best_a, best_b = t1, t2
                
    return best_a, best_b

# --- UI INTERFACE ---
st.title("🏆 CRICKET TEAM BALANCER")

# 1. ADD PLAYER SECTION
with st.expander("➕ Add New Player", expanded=True):
    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    name = c1.text_input("Name")
    bat_rating = c2.number_input("Batting (0-10)", 0, 10, 5)
    bowl_rating = c3.number_input("Bowling (0-10)", 0, 10, 5)
    
    # Added Tooltip (Help) for Booster
    boost = c4.number_input("Booster Points", 0, 10, 0, 
                            help="Extra influence points! Use this for Captains or Key Players who impact the game beyond just stats.")
    
    if st.button("ADD PLAYER"):
        if name:
            new_player = {
                "Name": name, 
                "Batting": bat_rating, 
                "Bowling": bowl_rating, 
                "Booster": boost
            }
            # Remove any old version of this player if name matches
            st.session_state.players = [p for p in st.session_state.players if p.get("Name") != name]
            st.session_state.players.append(new_player)
            save_data(st.session_state.players)
            st.rerun()

# 2. EDIT SQUAD SECTION
st.write("---")
st.subheader("📋 Current Squad")

if st.session_state.players:
    # Ensure we only show the relevant columns (Filtering out old 'Rating' column)
    df = pd.DataFrame(st.session_state.players)
    
    # Handle missing columns if older data exists
    for col in ['Batting', 'Bowling', 'Booster']:
        if col not in df.columns:
            df[col] = 0
            
    # Filter only the columns we want to see/edit
    df_display = df[['Name', 'Batting', 'Bowling', 'Booster']]
    
    # Editable Table
    edited_df = st.data_editor(
        df_display, 
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editor"
    )
    
    # Sync changes back to database
    current_data = edited_df.to_dict('records')
    # Only save if data actually changed (prevents infinite loops)
    # converting to list of dicts for comparison
    if len(current_data) != len(st.session_state.players) or current_data != [
        {k: p.get(k, 0) for k in ['Name', 'Batting', 'Bowling', 'Booster']} 
        for p in st.session_state.players
    ]:
        st.session_state.players = current_data
        save_data(st.session_state.players)

# 3. GENERATE TEAMS
st.write("---")
if len(st.session_state.players) >= 2:
    if st.button("⚡ GENERATE BALANCED TEAMS"):
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

            with col_a:
                st.markdown("### 🟡 TEAM GOLD")
                st.dataframe(pd.DataFrame(t1)[['Name', 'Batting', 'Bowling']], use_container_width=True, hide_index=True)
                st.success(f"🏏 Bat: {a_bat} | 🥎 Bowl: {a_bowl} | 💪 Total: {a_tot}")

            with col_b:
                st.markdown("### ⚫ TEAM BLACK")
                st.dataframe(pd.DataFrame(t2)[['Name', 'Batting', 'Bowling']], use_container_width=True, hide_index=True)
                st.warning(f"🏏 Bat: {b_bat} | 🥎 Bowl: {b_bowl} | 💪 Total: {b_tot}")
        else:
            st.error("⚠️ Could not find a perfect balance (Diff < 3). Try adjusting player ratings.")
