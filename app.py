import streamlit as st
import json
import time
from github import Github

# --- 1. GitHub連携設定 (Streamlit CloudのSecretsから取得) ---
try:
    token = st.secrets["GITHUB_TOKEN"]
    user = st.secrets["GITHUB_USER"]
    repo_name = st.secrets["GITHUB_REPO"]
    g = Github(token)
    repo = g.get_repo(f"{user}/{repo_name}")
except Exception as e:
    st.error("GitHub連携設定（Secrets）が未設定です。Streamlit Cloudの設定画面でSecretsを登録してください。")
    st.stop()

# --- 2. 基本設定・色定義 ---
DB_FILE = 'players.json'
POS_DATA = {
    "FW": ["LW", "CF", "RW"],
    "MF": ["LM", "RM", "AM", "DM"],
    "DF": ["LB", "RB", "CB"],
    "GK": ["GK"]
}
POLICY_OPTIONS = ["リアクション", "ポゼッション", "カウンター", "ムービング"]

st.set_page_config(page_title="サカつく2026 Web管理ツール", layout="wide")

# ポジション別のカラー設定 (CSS)
style_css = """
<style>
    span[data-baseweb="tag"]:has(span[title*="FW"]), span[data-baseweb="tag"]:has(span[title="LW"]), 
    span[data-baseweb="tag"]:has(span[title="CF"]), span[data-baseweb="tag"]:has(span[title="RW"]) 
    { background-color: #e8f5e9 !important; color: #2e7d32 !important; border: 1px solid #a5d6a7 !important; }
    span[data-baseweb="tag"]:has(span[title*="MF"]), span[data-baseweb="tag"]:has(span[title="LM"]), 
    span[data-baseweb="tag"]:has(span[title="RM"]), span[data-baseweb="tag"]:has(span[title="AM"]), span[data-baseweb="tag"]:has(span[title="DM"]) 
    { background-color: #fff3e0 !important; color: #ef6c00 !important; border: 1px solid #ffcc80 !important; }
    span[data-baseweb="tag"]:has(span[title*="DF"]), span[data-baseweb="tag"]:has(span[title="LB"]), 
    span[data-baseweb="tag"]:has(span[title="RB"]), span[data-baseweb="tag"]:has(span[title="CB"]) 
    { background-color: #e3f2fd !important; color: #1565c0 !important; border: 1px solid #90caf9 !important; }
    span[data-baseweb="tag"]:has(span[title*="GK"]) 
    { background-color: #ffebee !important; color: #c62828 !important; border: 1px solid #ef9a9a !important; }
</style>
"""
st.markdown(style_css, unsafe_allow_html=True)

# --- 3. セッション状態の初期化 ---
if "form_id" not in st.session_state:
    st.session_state.form_id = 0
fid = st.session_state.form_id

# キーの初期化
for key in [f"main_{fid}", f"sub_{fid}", f"old_sub_{fid}"]:
    if key not in st.session_state:
        st.session_state[key] = []

# --- 4. GitHub APIを使った読み書き関数 ---
@st.cache_data(ttl=60) # 1分間はキャッシュを利用して高速化
def load_data_from_github():
    try:
        contents = repo.get_contents(DB_FILE)
        return json.loads(contents.decoded_content.decode('utf-8'))
    except:
        return []

def save_data_to_github(data, message="Update players.json"):
    contents = repo.get_contents(DB_FILE)
    json_string = json.dumps(data, ensure_ascii=False, indent=4)
    repo.update_file(contents.path, message, json_string, contents.sha)
    st.cache_data.clear() # キャッシュをクリアして最新を読み込めるようにする

# --- 5. ポジション連動ロジック ---
def on_main_change():
    m_val = st.session_state[f"main_{fid}"]
    s_val = list(st.session_state[f"sub_{fid}"])
    if "GK" in m_val and "GK" not in s_val:
        s_val.append("GK")
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

# --- 6. メイン画面処理 ---
data = load_data_from_github()
st.title("⚽ サカつく2026 Web管理システム")
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
else:
    target_player = {}

st.write("---")
col1, col2 = st.columns(2)

with col1:
    name = st.text_input("選手名", value=target_player.get('name', ""), key=f"name_{fid}")
    st.multiselect("ポジション種別", ["FW", "MF", "DF", "GK"], key=f"main_{fid}", on_change=on_main_change)
    sub_options = []
    for m in st.session_state[f"main_{fid}"]:
        sub_options.extend(POS_DATA[m])
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

if st.button("💾 GitHubのデータを更新"):
    if not name or not st.session_state[f"main_{fid}"] or not st.session_state[f"sub_{fid}"]:
        st.error("選手名とポジションは必須です。")
    else:
        new_player = {
            "name": name, 
            "main_pos": st.session_state[f"main_{fid}"], 
            "sub_pos": st.session_state[f"sub_{fid}"], 
            "foot": foot, "hw": hw, "policy": policy, "growth": growth, "max_overall": max_overall,
            "style": style, "style_rank": style_rank, "inherit": inherit,
            "i_skill": i_skill, "i_trait": i_trait, "trait_lv": trait_lv,
            "personalities": [p.strip() for p in personalities.split(",") if p.strip()]
        }
        
        # 保存前に最新データをGitHubから取得して統合
        latest_data = load_data_from_github()
        if mode == "新規登録":
            latest_data.append(new_player)
            msg = f"Add new player: {name}"
        else:
            # 同じ名前の選手がいれば上書き
            latest_data = [new_player if p['name'] == target_player['name'] else p for p in latest_data]
            msg = f"Update player: {name}"
        
        # GitHubへ保存
        try:
            save_data_to_github(latest_data, message=msg)
            placeholder.success("✅ GitHubへの保存が完了しました！")
            time.sleep(1)
            if mode == "新規登録":
                st.session_state.form_id += 1
            st.rerun()
        except Exception as e:
            st.error(f"保存エラー: {e}")

if mode == "編集・削除" and st.button("🚨 削除する"):
    latest_data = load_data_from_github()
    latest_data = [p for p in latest_data if p['name'] != target_player['name']]
    save_data_to_github(latest_data, message=f"Delete player: {target_player['name']}")
    st.rerun()
