import streamlit as st
import pandas as pd
import json
import os
import random

# --- FILE DATABASE ---
DB_FILE = "players_db.json"

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(players):
    with open(DB_FILE, "w") as f:
        json.dump(players, f)

# --- STYLING ---
st.set_page_config(page_title="Gold & Black Balancer", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    .stButton>button { 
        background-color: #D4AF37 !important; 
        color: #000 !important; 
        border: 2px solid #D4AF37 !important;
        width: 100%; font-weight: bold;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div {
        background-color: #1a1a1a !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important;
    }
    .css-12w0qpk { border: 1px solid #D4AF37; padding: 20px; border-radius: 10px; }
    h1, h2, h3 { color: #D4AF37; text-align: center; }
    </style>
    """, unsafe_with_html=True)

# --- SESSION STATE ---
if 'players' not in st.session_state:
    st.session_state.players = load_data()

# --- HELPER FUNCTIONS ---
def get_player_scores(p):
    # Calculate specialized scores based on role
    bat = p['rating'] + p['booster'] if p['role'] in ['Batsman', 'All-rounder'] else (p['rating'] * 0.4) + p['booster']
    bowl = p['rating'] + p['booster'] if p['role'] in ['Bowler', 'All-rounder'] else (p['rating'] * 0.4) + p['booster']
    total = p['rating'] + (p['booster'] * 1.5) # Weighting booster higher for overall
    return bat, bowl, total

def balance_teams(players):
    if len(players) % 2 != 0: return None, None
    
    best_team_a, best_team_b = [], []
    min_diff = float('inf')
    
    # Try 500 random permutations to find the most balanced fit
    for _ in range(500):
        random.shuffle(players)
        mid = len(players) // 2
        t1, t2 = players[:mid], players[mid:]
        
        t1_bat = sum(get_player_scores(p)[0] for p in t1)
        t2_bat = sum(get_player_scores(p)[0] for p in t2)
        t1_bowl = sum(get_player_scores(p)[1] for p in t1)
        t2_bowl = sum(get_player_scores(p)[1] for p in t2)
        t1_total = sum(get_player_scores(p)[2] for p in t1)
        t2_total = sum(get_player_scores(p)[2] for p in t2)
        
        # Priority 1: Batting & Bowling diff <= 3
        if abs(t1_bat - t2_bat) <= 3 and abs(t1_bowl - t2_bowl) <= 3:
            # Priority 2: Minimize overall points diff
            total_diff = abs(t1_total - t2_total)
            if total_diff < min_diff:
                min_diff = total_diff
                best_team_a, best_team_b = t1, t2
                
    return best_team_a, best_team_b

# --- UI LAYOUT ---
st.title("🏆 CRICKET TEAM BALANCER")

# Player Entry Section
with st.container():
    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
    name = col1.text_input("Player Name")
    role = col2.selectbox("Role", ["Batsman", "Bowler", "All-rounder"])
    rating = col3.number_input("Rating (1-10)", 1, 10, 7)
    booster = col4.number_input("Booster Points", 0, 10, 0)
    
    if st.button("ADD PLAYER TO SQUAD"):
        if name:
            new_player = {"name": name, "role": role, "rating": rating, "booster": booster}
            st.session_state.players.append(new_player)
            save_data(st.session_state.players)
            st.rerun()

# Squad Management
st.write("---")
st.subheader("Current Squad")
if st.session_state.players:
    df = pd.DataFrame(st.session_state.players)
    st.table(df)
    if st.button("Clear All Players"):
        st.session_state.players = []
        save_data([])
        st.rerun()

# Generation Section
st.write("---")
if len(st.session_state.players) >= 2:
    if st.button("⚡ GENERATE BALANCED TEAMS"):
        t1, t2 = balance_teams(st.session_state.players)
        
        if t1:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 🟡 TEAM GOLD")
                st.dataframe(pd.DataFrame(t1)[['name', 'role']])
                st.info(f"Batting: {sum(get_player_scores(p)[0] for p in t1):.1f} | Bowling: {sum(get_player_scores(p)[1] for p in t1):.1f}")
            with c2:
                st.markdown("### ⚫ TEAM BLACK")
                st.dataframe(pd.DataFrame(t2)[['name', 'role']])
                st.info(f"Batting: {sum(get_player_scores(p)[0] for p in t2):.1f} | Bowling: {sum(get_player_scores(p)[1] for p in t2):.1f}")
        else:
            st.error("Could not find a perfect balance within a 3-point difference. Try adjusting ratings.")
