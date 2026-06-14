import streamlit as st
import base64
import os
import json
import random
import time
import re
from openai import OpenAI

# ==========================================
# 0. 初始化配置
# ==========================================
st.set_page_config(page_title="喵星人之家 · 命运之轮", page_icon="🐾", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "home"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tarot_step" not in st.session_state:
    st.session_state.tarot_step = "input_question"
if "draw_count" not in st.session_state:
    st.session_state.draw_count = 0
if "drawn_cards" not in st.session_state:
    st.session_state.drawn_cards = []
if "shuffled_deck" not in st.session_state:
    st.session_state.shuffled_deck = list(range(72))
if "tarot_q" not in st.session_state:
    st.session_state.tarot_q = ""

def go_home():
    st.session_state.page = "home"
    st.session_state.tarot_step = "input_question"
    st.session_state.draw_count = 0
    st.session_state.drawn_cards = []
    st.session_state.tarot_q = ""
    st.rerun()

# ==========================================
# 1. 图像处理辅助
# ==========================================
def get_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

bg_base64 = get_base64("素材.jpeg")
card_back_base64 = get_base64("塔罗牌背景.jpeg")
cat_head = get_base64("小猫头像.jpeg")
user_head = get_base64("用户头像.jpeg")

# ==========================================
# 2. 魔法 CSS 注入
# ==========================================
st.markdown(f"""
<style>
    .stApp {{
        background-image: url("data:image/png;base64,{bg_base64}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    .block-container {{ padding: 0 !important; max-width: 100% !important; }}
    header {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    [data-testid="stSidebar"] {{ display: none !important; }}
    [data-testid="collapsedControl"] {{ display: none !important; }}

    button, [data-testid="baseButton-primary"], [data-testid="baseButton-secondary"], div.stButton > button {{
        background-color: #FFFDF8 !important;
        color: #5D4037 !important;
        border: 2px solid #F4C085 !important;
        border-radius: 25px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        text-shadow: none !important;
    }}
    button:hover, [data-testid="baseButton-primary"]:hover, [data-testid="baseButton-secondary"]:hover, div.stButton > button:hover {{
        background-color: #F4C085 !important;
        color: #FFFFFF !important;
        border-color: #E89A4F !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 10px rgba(244, 192, 133, 0.4) !important;
    }}
</style>
""", unsafe_allow_html=True)

if st.session_state.page == "home":
    st.markdown("""
    <style>
        div.stButton > button { 
            padding: 15px 0 !important; 
            border-radius: 35px !important; 
            border-width: 3px !important; 
            box-shadow: 0 6px 15px rgba(0,0,0,0.1) !important; 
        }
        div.stButton > button p { 
            font-size: 28px !important; 
            margin: 0 !important; 
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <style>
        div.stButton > button {{ font-size: 18px !important; padding: 10px 25px !important; }}
        
        div[data-testid="stTextInput"] input {{
            background-color: #FFFFFF !important; 
            border: 2px solid #F4C085 !important; 
            border-radius: 20px !important;
            padding: 12px 20px !important; 
            font-size: 16px !important;
            color: #5D4037 !important;
            text-align: center;
        }}
        div[data-testid="stTextInput"] input:focus {{ box-shadow: 0 0 10px rgba(244, 192, 133, 0.5) !important; outline: none !important; }}
        div[data-testid="stTextInput"] label {{ display: none !important; }}

        .chat-box {{ max-width: 850px; margin: 0 auto; padding: 20px; }}
        .msg-row {{ display: flex; align-items: flex-start; margin-bottom: 25px; }}
        .msg-row.user {{ flex-direction: row-reverse; }}
        .avatar {{ width: 80px; height: 80px; border-radius: 50%; border: 3px solid #F4C085; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .bubble {{ max-width: 60%; padding: 15px 20px; font-size: 16px; position: relative; margin: 0 15px; border-radius: 20px; border: 2px solid #F4C085; background: #FFF8E1; color: #4E342E; line-height: 1.6; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        
        .shuffling-container {{ position: relative; height: 240px; display: flex; justify-content: center; align-items: center; margin: 20px 0; }}
        .mini-card {{ position: absolute; width: 110px; height: 180px; background-image: url("data:image/png;base64,{card_back_base64}"); background-size: cover; border-radius: 8px; border: 2px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }}
        .mini-card:nth-child(1) {{ transform: rotate(-25deg) translateX(-40px) translateY(20px); z-index: 1; animation: shuffle-left 0.5s infinite alternate ease-in-out; }}
        .mini-card:nth-child(2) {{ transform: rotate(0deg) translateX(0); z-index: 2; animation: shuffle-center 0.5s infinite alternate ease-in-out; }}
        .mini-card:nth-child(3) {{ transform: rotate(25deg) translateX(40px) translateY(20px); z-index: 3; animation: shuffle-right 0.5s infinite alternate ease-in-out; }}
        @keyframes shuffle-left {{ 0% {{ transform: rotate(-25deg) translateX(-40px) translateY(20px); }} 100% {{ transform: rotate(-5deg) translateX(-10px) translateY(-10px); }} }}
        @keyframes shuffle-center {{ 0% {{ transform: rotate(0deg) translateX(0); }} 100% {{ transform: rotate(0deg) translateX(0) translateY(15px); }} }}
        @keyframes shuffle-right {{ 0% {{ transform: rotate(25deg) translateX(40px) translateY(20px); }} 100% {{ transform: rotate(5deg) translateX(10px) translateY(-10px); }} }}
        
        .card-spread-row {{ display: flex; justify-content: center; gap: 20px; padding: 20px 0; }}
        .spread-card {{ width: 120px; height: 200px; background-image: url("data:image/png;base64,{card_back_base64}"); background-size: cover; background-position: center; border-radius: 8px; border: 2px solid #D4AF37; box-shadow: 2px 4px 8px rgba(0,0,0,0.2); transition: transform 0.3s ease; }}
        .spread-card:hover {{ transform: translateY(-10px); box-shadow: 2px 10px 15px rgba(0,0,0,0.3); }}
        .result-card-img {{ width: 130px; border-radius: 10px; border: 2px solid #F4C085; box-shadow: 0 4px 8px rgba(0,0,0,0.2); transition: transform 0.3s; }}
        .result-card-img:hover {{ transform: scale(1.05); }}
    </style>
    """, unsafe_allow_html=True)

# API 设置
client = OpenAI(api_key="42404344", base_url="https://handson.top/python2026/final-staging/api/deepseek/v1")

# --- 主页面逻辑 ---
if st.session_state.page == "home":
    st.markdown('<div style="height: 42vh;"></div>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns([1.2, 2, 1.5, 2, 1.2])
    with col2:
        if st.button("🔮 喵咪占卜 🔮", use_container_width=True):
            st.session_state.page = "tarot"
            st.rerun()
    with col4:
        if st.button("🧸 喵咪树洞 🧸", use_container_width=True):
            st.session_state.page = "chat"
            st.rerun()

# --- 喵咪树洞 ---
elif st.session_state.page == "chat":
    st.markdown("<br>", unsafe_allow_html=True)
    col_back, _ = st.columns([1.5, 6])
    with col_back:
        if st.button("🏠 返回主页面", use_container_width=True): go_home()

    st.markdown("""
    <div style="text-align:center; margin-bottom: 30px;">
        <span style="background-color: rgba(255, 253, 248, 0.9); border: 2px solid #F4C085; border-radius: 30px; padding: 10px 40px; font-size: 22px; font-weight: bold; color: #5D4037; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
             🧸 喵咪树洞 🧸
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        role = "assistant" if msg["role"] == "assistant" else "user"
        head = cat_head if msg["role"] == "assistant" else user_head
        st.markdown(f"""
        <div class="msg-row {role}">
            <img src="data:image/png;base64,{head}" class="avatar">
            <div class="bubble">{msg["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if prompt := st.chat_input("说出你的秘密..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.spinner("喵咪正在倾听..."):
            system_prompt = "你是一只治愈的树洞猫咪。请给出简短、温暖、贴心的回答，尽量控制在两三句话以内，不要长篇大论，多用'喵'等可爱的语气词。"
            resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role":"system","content":system_prompt}] + st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})
            st.rerun()

# --- 喵咪占卜 ---
elif st.session_state.page == "tarot":
    st.markdown("<br>", unsafe_allow_html=True)
    col_back, _ = st.columns([1.5, 6])
    with col_back:
        if st.button("🏠 返回主页面", use_container_width=True): go_home()

    st.markdown("""
    <div style="text-align:center; margin-bottom: 30px;">
        <span style="background-color: rgba(255, 253, 248, 0.95); border: 2px solid #F4C085; border-radius: 30px; padding: 10px 50px; font-size: 24px; font-weight: bold; color: #5D4037; box-shadow: 0 4px 8px rgba(0,0,0,0.05);">
            🔮 喵咪魔法占卜 🔮
        </span>
    </div>
    """, unsafe_allow_html=True)

    # 1. 输入问题
    if st.session_state.tarot_step == "input_question":
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("隐藏", placeholder="🔮 请将问题藏在心中，并在此写下命运的指引...", label_visibility="collapsed", key="tarot_q")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2, col_btn3 = st.columns([1.2, 1.5, 1.2])
        with col_btn2:
            if st.button("✨ 开始洗牌", use_container_width=True):
                if not st.session_state.tarot_q.strip():
                    st.markdown("""
                    <div style="background-color: #FFFFFF; border: 2px solid #F4C085; border-radius: 15px; padding: 15px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: 10px;">
                        <span style="color: #D35400; font-size: 16px; font-weight: bold;">🔮 命运之轮需要明确的指引，请先在上方输入您心中的问题哦喵~</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.session_state.tarot_question = st.session_state.tarot_q 
                    st.session_state.tarot_step = "shuffling"
                    st.rerun()

    # 2. 洗牌
    elif st.session_state.tarot_step == "shuffling":
        st.markdown("""
        <div class="shuffling-container">
            <div class="mini-card"></div>
            <div class="mini-card"></div>
            <div class="mini-card"></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:20px; color:#5D4037; font-weight:bold;'>命运之轮正在转动...</p>", unsafe_allow_html=True)
        time.sleep(2.5) 
        random.shuffle(st.session_state.shuffled_deck)
        st.session_state.tarot_step = "drawing"
        st.session_state.draw_count = 0
        st.session_state.drawn_cards = []
        st.rerun()

    # 3. 摆牌抽牌
    elif st.session_state.tarot_step == "drawing":
        spread_html = '<div class="card-spread-row">' + ''.join(['<div class="spread-card"></div>' for _ in range(6)]) + '</div>'
        st.markdown(spread_html, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        status = ["过去 / 起因", "现在 / 状态", "未来 / 建议"]
        for i in range(3):
            with [c1, c2, c3][i]:
                if i < st.session_state.draw_count:
                    st.markdown(f"<div style='text-align:center; color:#D35400; font-size:18px; font-weight:bold;'>✅ {status[i]}已落定</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:center; color:#8D6E63; font-size:18px; font-weight:bold;'>⏳ 等待命运指引</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.session_state.draw_count < 3:
            col1, col2, col3 = st.columns([1, 1.5, 1])
            with col2:
                if st.button(f"🐾 抽取第 {st.session_state.draw_count + 1} 张牌", use_container_width=True):
                    card_id = st.session_state.shuffled_deck.pop()
                    st.session_state.drawn_cards.append(card_id)
                    st.session_state.draw_count += 1
                    if st.session_state.draw_count == 3:
                        st.session_state.tarot_step = "result"
                    st.rerun()

    # 4. 结果展示
    elif st.session_state.tarot_step == "result":
        st.markdown("<p style='text-align:center; font-size:24px; color:#5D4037; font-weight:bold;'>🐾 翻开命运的低语 🐾</p><br>", unsafe_allow_html=True)
        
        res_cols = st.columns([1.5, 2, 2, 2, 1.5])
        positions = ["过去 / 起因", "现 在 / 状态", "未来 / 建议"]
        
        tarot_info_ui = {}     
        tarot_info_llm = {}    

        if os.path.exists("tarot_data.json"):
            try:
                with open("tarot_data.json", "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    if isinstance(raw_data, list):
                        for item in raw_data:
                            if isinstance(item, dict) and "id" in item:
                                cid = str(item["id"])
                                raw_name = item.get("name", "神秘卡牌")
                                meaning = item.get("upright", "卡牌正在细语...")
                                
                                cn_name = raw_name
                                if "(" in raw_name:
                                    cn_name = raw_name.split("(")[0].strip()
                                elif "（" in raw_name:
                                    cn_name = raw_name.split("（")[0].strip()
                                
                                tarot_info_ui[cid] = f"<div style='text-align:center; margin-bottom:10px;'><span style='font-size:16px; font-weight:bold; color:#D35400;'>【{cn_name}】</span></div><div style='text-align:center;'>{meaning}</div>"
                                tarot_info_llm[cid] = f"【{cn_name}】(正位牌意：{meaning})"
            except Exception:
                pass

        for i in range(3):
            card_id = st.session_state.drawn_cards[i]
            with res_cols[i+1]:
                st.markdown(f"<p style='text-align:center; margin-bottom:15px; color:#D35400; font-size:18px; font-weight:bold;'>{positions[i]}</p>", unsafe_allow_html=True)
                img_path = f"static/images/card_{card_id}.png"
                if os.path.exists(img_path):
                    st.markdown(f"""
                    <div style="text-align:center; margin-bottom:15px;">
                        <img src="data:image/png;base64,{get_base64(img_path)}" class="result-card-img">
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.write(f"🃏 牌面 {card_id}")
                
                msg_ui = tarot_info_ui.get(str(card_id), "<div style='text-align:center;'>卡牌正在细语...</div>")
                
                st.markdown(f"""
                <div style='background-color:#FFFFFF; padding:15px; border-radius:15px; border:2px solid #F4C085; box-shadow:0 2px 5px rgba(0,0,0,0.05);'>
                    <div style='font-size:14px; margin:0; line-height:1.6; color:#5D4037; text-align:center;'>{msg_ui}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([0.5, 2, 0.5])
        with col2:
            if st.button("🔮 获取命运综合解读", use_container_width=True):
                with st.spinner("塔罗导师凝视水晶球中..."):
                    llm_cards = [tarot_info_llm.get(str(cid), f"{cid}号牌") for cid in st.session_state.drawn_cards]
                    cards_str = "、".join(llm_cards)
                    
                    # ★★★ 核心升级提示词：严格命令大模型前文做正常叙述分析（绝不许标123），仅在最终建议处列出123！ ★★★
                    prompt = f"""
你现在是一位专业、资深、充满洞察力的神秘学塔罗占卜导师，同时也具备小猫的温柔与活力（可以适当使用“喵”字）。
用户心中的问题：'{st.session_state.tarot_question}'。
抽到的三张牌：{'、'.join(llm_cards)}。

【请严格遵循以下排版与结构进行回复】：
1. 开场：用导师的口吻向用户问好（包含猫咪的俏皮语气）。
2. 卡牌逐一分析：按“过去”、“现在”、“未来”三个维度解读。段落标题前请使用 Emoji（如 📜过去、🔥现在、⚔️未来），且严禁在该部分使用任何数字序号（1.2.3.）并且卡牌名字要用【】包裹，还要加粗。
3. 深度整合解读：必须使用【深度整合解读】作为标题，标题字体加粗。
4. 切实建议：必须使用【切实建议】作为标题，标题字体加粗。建议使用序号1.2.3.标注。序号与内容必须紧挨着在同一行（例如：1.扮演冷静的裁判），严禁换行。
5. 结束语：使用【结束语】作为标题，标题字体加粗，请根据整场解读的意境，自然地总结出一段充满尊严、智慧且富有力量的收尾寄语。不要用固定模板，要像一位睿智的导师给出的最终赠言。
【输出排版硬性约束】：
- 全文保持极度紧凑，拒绝段落之间的大幅度空行。
- 序号仅限“切实建议”部分，前面所有段落严禁序号。
- 请用深刻且睿智的指引语，让用户感受到“结构化理性”带来的力量。
- 不要出现**
"""
                    
                    resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompt}])
                    st.session_state.tarot_reading = resp.choices[0].message.content
            
            if getattr(st.session_state, "tarot_reading", "") != "":
                
                clean_reading = st.session_state.tarot_reading
                # 强力清除连续3个以上的富余空行
                clean_reading = re.sub(r'\n{3,}', '\n\n', clean_reading)
                
                # 按行切开，进行智能语意分类渲染
                raw_paragraphs = [p.strip() for p in clean_reading.split('\n') if p.strip()]
                html_paragraphs = ""
                
                for p in raw_paragraphs:
                    # 判断这一行是否是以数字序号开头 (如 "1." 或 "1、")
                    if re.match(r'^\d+[\.、]', p):
                        # ★★★ 精准去除数字后面的所有空格，变成干净紧凑的 "1.具体建议内容" ★★★
                        p_cleaned = re.sub(r'^(\d+[\.、])\s*', r'\1', p)
                        html_paragraphs += f"<p style='margin: 0 0 10px 0; text-indent: 2em; text-align: justify;'>{p_cleaned}</p>"
                    else:
                        # 普通的叙述段落：不带数字，正常首行缩进
                        html_paragraphs += f"<p style='margin: 0 0 10px 0; text-indent: 2em; text-align: justify;'>{p}</p>"
                
                st.markdown(f"""
                <div style="background-color:#FFFFFF; padding:25px 30px; border-radius:20px; border:3px dashed #F4C085; box-shadow:0 8px 20px rgba(0,0,0,0.1); margin-top:20px; margin-bottom:30px;">
                    <h3 style="text-align:center; color:#D35400; font-size:20px; margin-bottom:20px; font-weight:bold;">✨ 命运的综合指引 ✨</h3>
                    <div style="color:#5D4037; font-size:16px; line-height:1.8;">{html_paragraphs}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 再次占卜", use_container_width=True):
                go_home()

    st.markdown('</div>', unsafe_allow_html=True)
