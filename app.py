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
                    for p in data:
                        if 'Playing' not in p: p['Playing'] = True
                    return data
        except: return []
    return []

def save_data(players):
    with open(DB_FILE, "w") as f: json.dump(players, f)

# --- THEME & STYLING ---
st.set_page_config(page_title="Cricket Team Balancer", layout="centered") 
# Note: Changed layout to "centered" - looks better on mobile, still good on desktop

st.markdown("""
<style>
    /* MAIN BACKGROUND */
    .stApp { background-color: #000000; color: #D4AF37; }
    
    /* INPUTS & SELECTBOXES */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div, div[data-baseweb="popover"] { 
        background-color: #1a1a1a !important; 
        color: #D4AF37 !important; 
        border: 1px solid #D4AF37 !important; 
    }
    
    /* TABS Styling */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #D4AF37 !important;
        font-weight: bold;
    }
    button[data-baseweb="tab"]:hover {
        color: #FFFFFF !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: #D4AF37 !important;
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
    h1, h2, h3, h4, h5, p, label, .stMarkdown, .stCheckbox { color: #D4AF37 !important; }
    
    /* DATA EDITOR TABLE */
    div[data-testid="stDataEditor"] { border: 1px solid #D4AF37; border-radius: 5px; overflow: hidden; }
    
    /* MOBILE ADJUSTMENT FOR STATS BOX */
    .stat-box {
        background-color: #D4AF37; 
        padding: 15px; 
        border-radius: 8px; 
        color: black; 
        text-align: center; 
        font-weight: bold; 
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(255, 215, 0, 0.2);
    }
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

def balance_teams_with_constraints(active_players, locked_a, locked_b):
    pool = [p for p in active_players if p['Name'] not in locked_a and p['Name'] not in locked_b]
    team_a = [p for p in active_players if p['Name'] in locked_a]
    team_b = [p for p in active_players if p['Name'] in locked_b]
    
    best_a, best_b = [], []
    min_diff = float('inf')
    
    for _ in range(1000):
        random.shuffle(pool)
        mid = len(pool) // 2
        temp_a = team_a + pool[:mid]
        temp_b = team_b + pool[mid:]
        
        if abs(len(temp_a) - len(temp_b)) > 1: continue

        s1 = calculate_team_stats(temp_a)
        s2 = calculate_team_stats(temp_b)
        
        w_tot_a = s1[0] + s1[1] + (sum(p['Booster'] for p in temp_a) * 2)
        w_tot_b = s2[0] + s2[1] + (sum(p['Booster'] for p in temp_b) * 2)
        
        if abs(s1[0] - s2[0]) <= 3 and abs(s1[1] - s2[1]) <= 3:
            total_diff = abs(w_tot_a - w_tot_b)
            if total_diff < min_diff:
                min_diff = total_diff
                best_a, best_b = temp_a, temp_b
                
    if not best_a:
        mid = len(pool) // 2
        best_a = team_a + pool[:mid]
        best_b = team_b + pool[mid:]
        
    return best_a, best_b

# --- UI INTERFACE ---
st.title("🏆 CRICKET TEAM BALANCER")

# 1. ADD PLAYER (MOBILE OPTIMIZED: 2 Rows)
with st.expander("➕ Add New Player", expanded=False):
    # Row 1: Name and Role
    r1_c1, r1_c2 = st.columns([3, 2])
    name = r1_c1.text_input("Player Name")
    role = r1_c2.selectbox("Role", ["All-rounder", "Batsman", "Bowler"])
    
    # Row 2: Stats (Easier to tap on phone)
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    bat = r2_c1.number_input("Batting", 0, 10, 5)
    bowl = r2_c2.number_input("Bowling", 0, 10, 5)
    boost = r2_c3.number_input("Booster", 0, 10, 0, help="Extra value points")
    
    if st.button("ADD PLAYER"):
        if name:
            new_p = {"Name": name, "Role": role, "Batting": bat, "Bowling": bowl, "Booster": boost, "Playing": True}
            st.session_state.players = [p for p in st.session_state.players if p['Name'] != name]
            st.session_state.players.append(new_p)
            save_data(st.session_state.players)
            st.rerun()

# 2. MANAGE SQUAD
st.write("---")
if st.session_state.players:
    with st.expander("📋 View / Edit Squad", expanded=True):
        st.caption("Check the box to include player in today's match")
        df = pd.DataFrame(st.session_state.players)
        if 'Playing' not in df.columns: df['Playing'] = True
        
        # Use simple columns for mobile readability
        cols = ['Playing', 'Name', 'Role', 'Batting', 'Bowling', 'Booster']
        
        edited = st.data_editor(
            df[cols], 
            num_rows="dynamic", 
            use_container_width=True, 
            key="editor",
            column_config={
                "Playing": st.column_config.CheckboxColumn("Play?", default=True),
                "Name": st.column_config.TextColumn("Name", width="medium"),
            }
        )
        
        curr = edited.to_dict('records')
        if len(curr) != len(st.session_state.players) or curr != [{k:p.get(k,0 if k not in ['Name','Role'] else (True if k=='Playing' else '')) for k in cols} for p in st.session_state.players]:
            st.session_state.players = curr
            save_data(st.session_state.players)
            st.rerun()

    active_players = [p for p in st.session_state.players if p.get('Playing', True)]
    st.markdown(f"**✅ Playing Today:** {len(active_players)}")

# 3. TEAM GENERATION
st.write("---")
st.subheader("⚙️ Generate Teams")

if 'active_players' in locals() and len(active_players) >= 2:
    # On mobile, these will stack automatically
    col_lock1, col_lock2 = st.columns(2)
    active_names = [p['Name'] for p in active_players]
    
    with col_lock1:
        lock_gold = st.multiselect("Force into GOLD", active_names)
    with col_lock2:
        avail_black = [p for p in active_names if p not in lock_gold]
        lock_black = st.multiselect("Force into BLACK", avail_black)

    if st.button("⚡ GENERATE / RE-ROLL TEAMS"):
        t1, t2 = balance_teams_with_constraints(active_players, lock_gold, lock_black)
        st.session_state.team_a = t1
        st.session_state.team_b = t2
        st.rerun()
elif 'active_players' in locals():
    st.error("Select at least 2 players to generate.")

# 4. RESULTS (MOBILE OPTIMIZED: Tabs)
if st.session_state.team_a and st.session_state.team_b:
    st.write("---")
    
    a_bat, a_bowl, a_tot = calculate_team_stats(st.session_state.team_a)
    b_bat, b_bowl, b_tot = calculate_team_stats(st.session_state.team_b)
    
    # Custom Function for Stats Display
    def stats_box(bat, bowl, boost, tot):
        return f"""
        <div class="stat-box">
            <div>🏏 Bat: {bat} | 🥎 Bowl: {bowl} | ✨ Boost: {boost}</div>
            <div style="font-size: 20px; margin-top: 5px; text-decoration: underline;">TOTAL POINTS: {tot}</div>
        </div>
        """
    
    cols = ['Name', 'Role', 'Batting', 'Bowling', 'Booster']

    # TABS - This is the key change for Mobile
    tab1, tab2 = st.tabs(["🟡 TEAM GOLD", "⚫ TEAM BLACK"])

    with tab1:
        st.markdown(stats_box(a_bat, a_bowl, sum(p['Booster'] for p in st.session_state.team_a), a_tot), unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(st.session_state.team_a)[cols], use_container_width=True, hide_index=True)
        
    with tab2:
        st.markdown(stats_box(b_bat, b_bowl, sum(p['Booster'] for p in st.session_state.team_b), b_tot), unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(st.session_state.team_b)[cols], use_container_width=True, hide_index=True)

    # SWAP UI
    st.write("---")
    with st.expander("🔄 Swap Players", expanded=False):
        sc1, sc2 = st.columns(2)
        swap_a = sc1.selectbox("From Gold", [p['Name'] for p in st.session_state.team_a])
        swap_b = sc2.selectbox("From Black", [p['Name'] for p in st.session_state.team_b])
        
        if st.button("↔️ Confirm Swap"):
            p_a = next(p for p in st.session_state.team_a if p['Name'] == swap_a)
            p_b = next(p for p in st.session_state.team_b if p['Name'] == swap_b)
            st.session_state.team_a.remove(p_a)
            st.session_state.team_b.remove(p_b)
            st.session_state.team_a.append(p_b)
            st.session_state.team_b.append(p_a)
            st.rerun()
