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
                if isinstance(data, list): return data
        except: return []
    return []

def save_data(players):
    with open(DB_FILE, "w") as f: json.dump(players, f)

# --- THEME & STYLING ---
st.set_page_config(page_title="Cricket Team Balancer", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #000000; color: #D4AF37; }
    
    /* INPUTS & SELECTBOXES */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div, div[data-baseweb="popover"] { 
        background-color: #1a1a1a !important; 
        color: #D4AF37 !important; 
        border: 1px solid #D4AF37 !important; 
    }
    
    /* DROPDOWN OPTIONS */
    ul[data-testid="stSelectboxVirtualDropdown"] { background-color: #1a1a1a !important; }
    li[role="option"] { color: #D4AF37 !important; }
    
    /* BUTTONS */
    div.stButton > button { 
        background-color: #D4AF37 !important; 
        color: #000000 !important; 
        font-weight: 900 !important;
        border: none !important;
        font-size: 16px !important;
    }
    div.stButton > button:hover { background-color: #F4CF57 !important; color: black !important; }
    div.stButton > button p { color: black !important; }

    /* TEXT COLORS */
    h1, h2, h3, h4, h5, p, label, .stMarkdown { color: #D4AF37 !important; }
    
    /* SUCCESS/WARNING BOXES TEXT FIX */
    .stAlert div[data-testid="stMarkdownContainer"] > p { color: black !important; font-weight: bold; }

    /* DATA EDITOR */
    div[data-testid="stDataEditor"] { border: 1px solid #D4AF37; border-radius: 5px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

if 'players' not in st.session_state: st.session_state.players = load_data()
if 'team_a' not in st.session_state: st.session_state.team_a = []
if 'team_b' not in st.session_state: st.session_state.team_b = []

# --- HELPER FUNCTIONS ---
def calculate_team_stats(team):
    bat = sum(p.get('Batting', 0) for p in team)
    bowl = sum(p.get('Bowling', 0) for p in team)
    boost = sum(p.get('Booster', 0) for p in team)
    total = bat + bowl + boost
    return bat, bowl, total

def balance_teams_with_constraints(all_players, locked_a, locked_b):
    # Separate available pool from locked players
    pool = [p for p in all_players if p['Name'] not in locked_a and p['Name'] not in locked_b]
    
    # Get the locked player objects
    team_a = [p for p in all_players if p['Name'] in locked_a]
    team_b = [p for p in all_players if p['Name'] in locked_b]
    
    best_a, best_b = [], []
    min_diff = float('inf')
    
    # Run iterations to balance the REMAINING pool
    for _ in range(1000):
        random.shuffle(pool)
        mid = len(pool) // 2
        # Distribute pool
        temp_a = team_a + pool[:mid]
        temp_b = team_b + pool[mid:]
        
        # Check basic size balance (allow difference of 1)
        if abs(len(temp_a) - len(temp_b)) > 1: continue

        s1 = calculate_team_stats(temp_a)
        s2 = calculate_team_stats(temp_b)
        
        # Weighted comparison for algorithm (Booster * 2)
        # We use weighted logic for sorting, but simple math for display
        w_tot_a = s1[0] + s1[1] + (sum(p['Booster'] for p in temp_a) * 2)
        w_tot_b = s2[0] + s2[1] + (sum(p['Booster'] for p in temp_b) * 2)
        
        bat_diff = abs(s1[0] - s2[0])
        bowl_diff = abs(s1[1] - s2[1])
        
        if bat_diff <= 3 and bowl_diff <= 3:
            total_diff = abs(w_tot_a - w_tot_b)
            if total_diff < min_diff:
                min_diff = total_diff
                best_a, best_b = temp_a, temp_b
                
    # Fallback if no perfect match found (just split evenly)
    if not best_a:
        mid = len(pool) // 2
        best_a = team_a + pool[:mid]
        best_b = team_b + pool[mid:]
        
    return best_a, best_b

# --- UI INTERFACE ---
st.title("🏆 CRICKET TEAM BALANCER")

# 1. ADD PLAYER
with st.expander("➕ Add New Player", expanded=False):
    c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
    name = c1.text_input("Name")
    role = c2.selectbox("Role", ["All-rounder", "Batsman", "Bowler"])
    bat = c3.number_input("Batting", 0, 10, 5)
    bowl = c4.number_input("Bowling", 0, 10, 5)
    boost = c5.number_input("Booster", 0, 10, 0, help="Extra points for influence.")
    
    if st.button("ADD PLAYER"):
        if name:
            new_p = {"Name": name, "Role": role, "Batting": bat, "Bowling": bowl, "Booster": boost}
            st.session_state.players = [p for p in st.session_state.players if p['Name'] != name]
            st.session_state.players.append(new_p)
            save_data(st.session_state.players)
            st.rerun()

# 2. MANAGE SQUAD
st.write("---")
if st.session_state.players:
    with st.expander("📋 View / Edit Squad", expanded=True):
        df = pd.DataFrame(st.session_state.players)
        for c in ['Batting','Bowling','Booster']: df[c] = df.get(c, 0)
        edited = st.data_editor(df[['Name','Role','Batting','Bowling','Booster']], num_rows="dynamic", use_container_width=True, key="editor")
        
        curr = edited.to_dict('records')
        if len(curr) != len(st.session_state.players) or curr != [{k:p.get(k,0 if k!='Role' else '') for k in ['Name','Role','Batting','Bowling','Booster']} for p in st.session_state.players]:
            st.session_state.players = curr
            save_data(st.session_state.players)

# 3. TEAM GENERATION & CONSTRAINTS
st.write("---")
st.subheader("⚙️ Generate Teams")

if len(st.session_state.players) >= 2:
    col_lock1, col_lock2 = st.columns(2)
    player_names = [p['Name'] for p in st.session_state.players]
    
    # CONSTRAINTS INPUTS
    with col_lock1:
        lock_gold = st.multiselect("🔒 Force into TEAM GOLD", player_names)
    with col_lock2:
        # Filter out players already selected for Gold to avoid duplicates
        avail_black = [p for p in player_names if p not in lock_gold]
        lock_black = st.multiselect("🔒 Force into TEAM BLACK", avail_black)

    if st.button("⚡ GENERATE / RE-ROLL TEAMS"):
        t1, t2 = balance_teams_with_constraints(st.session_state.players, lock_gold, lock_black)
        st.session_state.team_a = t1
        st.session_state.team_b = t2
        st.rerun()

# 4. RESULTS & SWAP INTERFACE
if st.session_state.team_a and st.session_state.team_b:
    st.write("---")
    
    # Calculate current stats
    a_bat, a_bowl, a_tot = calculate_team_stats(st.session_state.team_a)
    b_bat, b_bowl, b_tot = calculate_team_stats(st.session_state.team_b)
    
    # DISPLAY TEAMS
    c1, c2 = st.columns(2)
    cols = ['Name', 'Role', 'Batting', 'Bowling', 'Booster']
    
    with c1:
        st.markdown(f"### 🟡 TEAM GOLD ({len(st.session_state.team_a)})")
        st.dataframe(pd.DataFrame(st.session_state.team_a)[cols], use_container_width=True, hide_index=True)
        st.success(f"🏏 Bat: {a_bat} | 🥎 Bowl: {a_bowl} | ✨ Booster: {sum(p['Booster'] for p in st.session_state.team_a)} | **TOTAL: {a_tot}**")
        
    with c2:
        st.markdown(f"### ⚫ TEAM BLACK ({len(st.session_state.team_b)})")
        st.dataframe(pd.DataFrame(st.session_state.team_b)[cols], use_container_width=True, hide_index=True)
        st.warning(f"🏏 Bat: {b_bat} | 🥎 Bowl: {b_bowl} | ✨ Booster: {sum(p['Booster'] for p in st.session_state.team_b)} | **TOTAL: {b_tot}**")

    # MANUAL SWAP SECTION
    st.write("---")
    with st.container():
        st.subheader("🔄 Manual Player Swap")
        sc1, sc2, sc3 = st.columns([4, 1, 4])
        
        swap_a = sc1.selectbox("Move from Team Gold", [p['Name'] for p in st.session_state.team_a])
        swap_b = sc3.selectbox("Move from Team Black", [p['Name'] for p in st.session_state.team_b])
        
        if sc2.button("↔️ SWAP"):
            # Find the actual player objects
            p_a = next(p for p in st.session_state.team_a if p['Name'] == swap_a)
            p_b = next(p for p in st.session_state.team_b if p['Name'] == swap_b)
            
            # Execute Swap
            st.session_state.team_a.remove(p_a)
            st.session_state.team_b.remove(p_b)
            st.session_state.team_a.append(p_b)
            st.session_state.team_b.append(p_a)
            st.rerun()
