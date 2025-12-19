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
                return json.load(f)
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
    .stApp { background-color: #000000; color: #FFFFFF; }
    .stButton>button { 
        background-color: #D4AF37 !important; 
        color: #000000 !important; 
        font-weight: bold !important;
        border: none !important;
        width: 100%;
    }
    input, div[data-baseweb="select"] > div { 
        background-color: #1a1a1a !important; 
        color: #D4AF37 !important; 
        border: 1px solid #D4AF37 !important; 
    }
    h1, h2, h3, h4, h5, p { color: #D4AF37; }
    /* Style for the editable dataframe */
    .stDataFrame { border: 1px solid #D4AF37; }
    div[data-testid="stDataFrame"] > div { background-color: #1a1a1a; color: white; }
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
        
        # Calculate stats directly from user inputs
        t1_bat = sum(p['Batting'] for p in t1)
        t2_bat = sum(p['Batting'] for p in t2)
        
        t1_bowl = sum(p['Bowling'] for p in t1)
        t2_bowl = sum(p['Bowling'] for p in t2)
        
        # Total power includes Booster weight
        t1_tot = t1_bat + t1_bowl + sum(p['Booster'] * 2 for p in t1)
        t2_tot = t2_bat + t2_bowl + sum(p['Booster'] * 2 for p in t2)
        
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
    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    name = c1.text_input("Name")
    # Separate inputs for Batting and Bowling
    bat_rating = c2.number_input("Batting (0-10)", 0, 10, 5)
    bowl_rating = c3.number_input("Bowling (0-10)", 0, 10, 5)
    boost = c4.number_input("Booster Points", 0, 10, 0)
    
    if st.button("ADD PLAYER"):
        if name:
            new_player = {
                "Name": name, 
                "Batting": bat_rating, 
                "Bowling": bowl_rating, 
                "Booster": boost
            }
            st.session_state.players.append(new_player)
            save_data(st.session_state.players)
            st.rerun()

# 2. EDIT SQUAD SECTION
st.write("---")
st.subheader("📋 Current Squad (Edit Here)")
st.info("💡 Tip: You can click on any cell below to edit the Name, Ratings, or Booster points directly!")

if st.session_state.players:
    # Convert list to DataFrame for editing
    df = pd.DataFrame(st.session_state.players)
    
    # The Data Editor allows direct editing
    edited_df = st.data_editor(
        df, 
        num_rows="dynamic",  # Allows user to delete rows
        use_container_width=True,
        hide_index=True,
        key="editor"
    )
    
    # Save changes automatically if user edits the table
    current_data = edited_df.to_dict('records')
    if current_data != st.session_state.players:
        st.session_state.players = current_data
        save_data(st.session_state.players)

# 3. GENERATE TEAMS
st.write("---")
if len(st.session_state.players) >= 2:
    if st.button("⚡ GENERATE BALANCED TEAMS"):
        t1, t2 = balance_teams(st.session_state.players)
        
        if t1:
            col_a, col_b = st.columns(2)
            
            # Helper to calculate team stats
            def get_stats(team):
                bat = sum(p['Batting'] for p in team)
                bowl = sum(p['Bowling'] for p in team)
                tot = bat + bowl + sum(p['Booster']*2 for p in team)
                return bat, bowl, tot

            a_bat, a_bowl, a_tot = get_stats(t1)
            b_bat, b_bowl, b_tot = get_stats(t2)

            with col_a:
                st.markdown("### 🟡 TEAM GOLD")
                st.table(pd.DataFrame(t1)[['Name', 'Batting', 'Bowling', 'Booster']])
                st.success(f"🏏 Bat: {a_bat} | 🥎 Bowl: {a_bowl} | 💪 Total Power: {a_tot}")

            with col_b:
                st.markdown("### ⚫ TEAM BLACK")
                st.table(pd.DataFrame(t2)[['Name', 'Batting', 'Bowling', 'Booster']])
                st.warning(f"🏏 Bat: {b_bat} | 🥎 Bowl: {b_bowl} | 💪 Total Power: {b_tot}")
        else:
            st.error("⚠️ Could not find a perfect balance (Diff < 3). Try adjusting player ratings or adding more players.")
