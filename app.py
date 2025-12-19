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

# Corrected Markdown block to prevent deployment errors
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
    h1, h2, h3 { color: #D4AF37; text-align: center; }
    .stDataFrame { border: 1px solid #D4AF37; }
</style>
""", unsafe_with_html=True)

if 'players' not in st.session_state:
    st.session_state.players = load_data()

# --- HELPER FUNCTIONS ---
def get_scores(p):
    # Overall points logic with Booster priority
    # Booster is weighted higher to ensure influence
    bat = p['Rating'] + p['Booster'] if p['Role'] in ['Batsman', 'All-rounder'] else (p['Rating'] * 0.5) + p['Booster']
    bowl = p['Rating'] + p['Booster'] if p['Role'] in ['Bowler', 'All-rounder'] else (p['Rating'] * 0.5) + p['Booster']
    total = p['Rating'] + (p['Booster'] * 2) 
    return bat, bowl, total

def balance_teams(players):
    best_a, best_b = [], []
    min_overall_diff = float('inf')
    
    # Run iterations to find the best split
    for _ in range(1000):
        random.shuffle(players)
        mid = len(players) // 2
        t1, t2 = players[:mid], players[mid:]
        
        t1_scores = [get_scores(p) for p in t1]
        t2_scores = [get_scores(p) for p in t2]
        
        t1_bat, t1_bowl, t1_tot = sum(s[0] for s in t1_scores), sum(s[1] for s in t1_scores), sum(s[2] for s in t1_scores)
        t2_bat, t2_bowl, t2_tot = sum(s[0] for s in t2_scores), sum(s[1] for s in t2_scores), sum(s[2] for s in t2_scores)
        
        # Check constraints: Batting and Bowling diff <= 3
        if abs(t1_bat - t2_bat) <= 3 and abs(t1_bowl - t2_bowl) <= 3:
            overall_diff = abs(t1_tot - t2_tot)
            if overall_diff < min_overall_diff:
                min_overall_diff = overall_diff
                best_a, best_b = t1, t2
                
    return best_a, best_b

# --- UI INTERFACE ---
st.title("🏆 CRICKET TEAM BALANCER")

# Player Entry
with st.container():
    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    name = c1.text_input("Player Name")
    role = c2.selectbox("Role", ["Batsman", "Bowler", "All-rounder"])
    rating = c3.number_input("Rating (1-10)", 1, 10, 5)
    boost = c4.number_input("Booster Points", 0, 10, 0)
    
    if st.button("ADD PLAYER"):
        if name:
            st.session_state.players.append({"Name": name, "Role": role, "Rating": rating, "Booster": boost})
            save_data(st.session_state.players)
            st.rerun()

# Squad and Edit Section
if st.session_state.players:
    st.write("---")
    st.subheader("Current Squad")
    for i, p in enumerate(st.session_state.players):
        col_name, col_edit, col_del = st.columns([0.7, 0.15, 0.15])
        col_name.write(f"**{p['Name']}** ({p['Role']}) - Rating: {p['Rating']} | Boost: {p['Booster']}")
        
        # Basic Delete functionality serves as "Edit" (Remove and re-add)
        if col_del.button("Delete", key=f"del_{i}"):
            st.session_state.players.pop(i)
            save_data(st.session_state.players)
            st.rerun()

    st.write("---")
    if len(st.session_state.players) >= 2:
        if st.button("⚡ GENERATE BALANCED TEAMS"):
            t1, t2 = balance_teams(st.session_state.players)
            if t1:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("### 🟡 TEAM GOLD")
                    st.table(pd.DataFrame(t1)[['Name', 'Role']])
                with col_b:
                    st.markdown("### ⚫ TEAM BLACK")
                    st.table(pd.DataFrame(t2)[['Name', 'Role']])
            else:
                st.error("Could not find a balance within 3 points. Try adding more players or adjusting ratings!")
