import streamlit as st
import json
import os
import time

# --- 設定・色定義 ---
DB_FILE = 'players.json'
POS_DATA = {
    "FW": ["LW", "CF", "RW"],
    "MF": ["LM", "RM", "AM", "DM"],
    "DF": ["LB", "RB", "CB"],
    "GK": ["GK"]
}
POLICY_OPTIONS = ["リアクション", "ポゼッション", "カウンター", "ムービング"]

# ポジション別のカラー設定 (CSS用)
POS_COLORS = {
    "FW": {"bg": "#e8f5e9", "text": "#2e7d32", "border": "#a5d6a7"},
    "MF": {"bg": "#fff3e0", "text": "#ef6c00", "border": "#ffcc80"},
    "DF": {"bg": "#e3f2fd", "text": "#1565c0", "border": "#90caf9"},
    "GK": {"bg": "#ffebee", "text": "#c62828", "border": "#ef9a9a"}
}

st.set_page_config(page_title="サカつく2026 管理ツール", layout="wide")

# --- カスタムCSSの注入 (マルチセレクトのタグに色をつける) ---
# ※Streamlitの内部構造に合わせたハック的CSSです
style_css = f"""
<style>
    /* FWタグ */
    span[data-baseweb="tag"]:has(span[title*="FW"]), span[data-baseweb="tag"]:has(span[title="LW"]), 
    span[data-baseweb="tag"]:has(span[title="CF"]), span[data-baseweb="tag"]:has(span[title="RW"]) 
    {{ background-color: {POS_COLORS['FW']['bg']} !important; color: {POS_COLORS['FW']['text']} !important; border: 1px solid {POS_COLORS['FW']['border']} !important; }}
    
    /* MFタグ */
    span[data-baseweb="tag"]:has(span[title*="MF"]), span[data-baseweb="tag"]:has(span[title="LM"]), 
    span[data-baseweb="tag"]:has(span[title="RM"]), span[data-baseweb="tag"]:has(span[title="AM"]), span[data-baseweb="tag"]:has(span[title="DM"]) 
    {{ background-color: {POS_COLORS['MF']['bg']} !important; color: {POS_COLORS['MF']['text']} !important; border: 1px solid {POS_COLORS['MF']['border']} !important; }}
    
    /* DFタグ */
    span[data-baseweb="tag"]:has(span[title*="DF"]), span[data-baseweb="tag"]:has(span[title="LB"]), 
    span[data-baseweb="tag"]:has(span[title="RB"]), span[data-baseweb="tag"]:has(span[title="CB"]) 
    {{ background-color: {POS_COLORS['DF']['bg']} !important; color: {POS_COLORS['DF']['text']} !important; border: 1px solid {POS_COLORS['DF']['border']} !important; }}
    
    /* GKタグ */
    span[data-baseweb="tag"]:has(span[title*="GK"]) 
    {{ background-color: {POS_COLORS['GK']['bg']} !important; color: {POS_COLORS['GK']['text']} !important; border: 1px solid {POS_COLORS['GK']['border']} !important; }}
</style>
"""
st.markdown(style_css, unsafe_allow_html=True)

# --- 以下、前回のロジックを継続 ---
if "form_id" not in st.session_state: st.session_state.form_id = 0
fid = st.session_state.form_id

if f"main_{fid}" not in st.session_state: st.session_state[f"main_{fid}"] = []
if f"sub_{fid}" not in st.session_state: st.session_state[f"sub_{fid}"] = []
if f"old_sub_{fid}" not in st.session_state: st.session_state[f"old_sub_{fid}"] = []

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return []

def save_data(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)

def on_main_change():
    m_val = st.session_state[f"main_{fid}"]
    s_val = list(st.session_state[f"sub_{fid}"])
    if "GK" in m_val and "GK" not in s_val: s_val.append("GK")
    s_val = [s for s in s_val if any(s in POS_DATA[m] for m in m_val)]
    st.session_state[f"sub_{fid}"] = s_val
    st.session_state[f"old_sub_{fid}"] = s_val

def on_sub_change():
    new_subs = list(st.session_state[f"sub_{fid}"])
    old_subs = st.session_state[f"old_sub_{fid}"]
    mains = list(st.session_state[f"main_{fid}"])
    removed_items = set(old_subs) - set(new_subs)
    for r_item in removed_items:
        parent_cat = next((m for m, s_list in POS_DATA.items() if r_item in s_list), None)
        if parent_cat:
            if not [s for s in new_subs if s in POS_DATA[parent_cat]]:
                if parent_cat in mains: mains.remove(parent_cat)
    st.session_state[f"main_{fid}"] = mains
    st.session_state[f"old_sub_{fid}"] = new_subs

data = load_data()
st.title("⚽ 選手データ管理システム")
mode = st.sidebar.radio("モード選択", ["新規登録", "編集・削除"])

if mode == "編集・削除" and data:
    player_names = [p['name'] for p in data]
    selected_name = st.selectbox("編集する選手を選択", player_names)
    target_index = player_names.index(selected_name)
    target_player = data[target_index]
    if st.session_state.get('last_selected_edit') != selected_name:
        st.session_state[f"main_{fid}"] = target_player.get('main_pos', [])
        st.session_state[f"sub_{fid}"] = target_player.get('sub_pos', [])
        st.session_state[f"old_sub_{fid}"] = target_player.get('sub_pos', [])
        st.session_state['last_selected_edit'] = selected_name
else: target_player = {}

st.write("---")
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("選手名", value=target_player.get('name', ""), key=f"name_{fid}")
    st.multiselect("ポジション種別", ["FW", "MF", "DF", "GK"], key=f"main_{fid}", on_change=on_main_change)
    sub_options = []
    for m in st.session_state[f"main_{fid}"]: sub_options.extend(POS_DATA[m])
    sub_options = sorted(list(set(sub_options)))
    st.multiselect("詳細ポジション", options=sub_options, key=f"sub_{fid}", on_change=on_sub_change)
    foot = st.selectbox("利き足", ["右", "左", "両"], index=["右", "左", "両"].index(target_player.get('foot', "右")), key=f"foot_{fid}")
    hw = st.text_input("身長/体重", value=target_player.get('hw', ""), key=f"hw_{fid}")
    policy_idx = POLICY_OPTIONS.index(target_player.get('policy', "カウンター")) if target_player.get('policy') in POLICY_OPTIONS else 0
    policy = st.selectbox("ポリシー", POLICY_OPTIONS, index=policy_idx, key=f"policy_{fid}")
    growth = st.selectbox("成長速度", ["早熟", "普通", "晩成"], index=["早熟", "普通", "晩成"].index(target_player.get('growth', "普通")), key=f"growth_{fid}")
    max_overall = st.number_input("最大総合力", 0, 20000, value=int(target_player.get('max_overall', 0)), key=f"overall_{fid}")

with col2:
    style = st.text_input("プレイスタイル", value=target_player.get('style', ""), key=f"style_{fid}")
    style_rank = st.selectbox("スタイルランク", ["Ⅰ", "Ⅱ", "Ⅲ"], index=["Ⅰ", "Ⅱ", "Ⅲ"].index(target_player.get('style_rank', "Ⅰ")), key=f"rank_{fid}")
    inherit = st.selectbox("継承可否", ["可", "不可"], index=["可", "不可"].index(target_player.get('inherit', "不可")), key=f"inherit_{fid}")
    if inherit == "不可":
        st.info("継承不可")
        i_skill, i_trait, trait_lv = "", "", 1
    else:
        i_skill = st.text_input("継承スキル", value=target_player.get('i_skill', ""), key=f"skill_{fid}")
        trait_disabled = True if i_skill else False
        i_trait = st.text_input("継承特徴", value=target_player.get('i_trait', "") if not i_skill else "", disabled=trait_disabled, key=f"trait_{fid}")
        trait_lv = st.number_input("特徴レベル", 1, 5, value=int(target_player.get('trait_lv', 1)) if not i_skill else 1, disabled=trait_disabled, key=f"lv_{fid}")
    st.write("---")
    pers_default = ",".join(target_player.get('personalities', []))
    personalities = st.text_area("個性 (カンマ区切り)", value=pers_default, key=f"pers_{fid}")

st.write("---")
placeholder = st.empty()
if st.button("💾 データを保存・更新"):
    if not name or not st.session_state[f"main_{fid}"] or not st.session_state[f"sub_{fid}"]:
        st.error("選手名とポジションは必須です。")
    else:
        new_player = {
            "name": name, "main_pos": st.session_state[f"main_{fid}"], "sub_pos": st.session_state[f"sub_{fid}"], 
            "foot": foot, "hw": hw, "policy": policy, "growth": growth, "max_overall": max_overall,
            "style": style, "style_rank": style_rank, "inherit": inherit, "i_skill": i_skill, "i_trait": i_trait, "trait_lv": trait_lv,
            "personalities": [p.strip() for p in personalities.split(",") if p.strip()]
        }
        if mode == "新規登録": data.append(new_player)
        else: data[target_index] = new_player
        save_data(data)
        placeholder.success("✅ 登録完了")
        time.sleep(1)
        placeholder.empty()
        if mode == "新規登録": st.session_state.form_id += 1
        st.rerun()

if mode == "編集・削除" and st.button("🚨 削除する"):
    del data[target_index]
    save_data(data)
    st.rerun()