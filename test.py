"""
30-Day Journaling Challenge — Streamlit App
Deploy: streamlit run journal_app.py
Requires: pip install streamlit bcrypt PyJWT pymongo
Set env vars: MONGO_URI, JWT_SECRET (optional, defaults provided for local dev)
"""

import streamlit as st
import bcrypt
import jwt
import os
import re
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError

# ── Config ────────────────────────────────────────────────────────────────────
MONGO_URI   = os.getenv("MONGO_URI", "mongodb+srv://sakshi-dasavekar:sakshi1024@cluster0.70iweve.mongodb.net/?appName=Cluster0")
JWT_SECRET  = os.getenv("JWT_SECRET", "change_me_in_production")
JWT_EXPIRY  = 30  # days

st.set_page_config(
    page_title="30-Day Journaling Challenge",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 30 Prompts ────────────────────────────────────────────────────────────────
PROMPTS = [
    {"theme": "The Origin Story", "tag": "Identity", "preview": "Trace who you are back to where it all began.", "prompt": "Every version of you was built on something. Write about the single experience, place, or person that most shaped who you are today. Don't rush to the conclusion — linger in the details. What did it smell like? Who else was there? Why do you think it stuck? Then ask yourself: is that shaping still serving you, or are you carrying it out of habit?"},
    {"theme": "The Emotion You Won't Name", "tag": "Emotional Depth", "preview": "There's something you've been feeling but not saying.", "prompt": "Somewhere beneath your daily routine, something is humming. What feeling have you been avoiding naming this week? Write it down — even if the word feels too big or too dramatic. Where does it live in your body? What sets it off? What would it say if you let it speak for five full minutes without interruption?"},
    {"theme": "Dear Future Me", "tag": "Vision", "preview": "Write to the person you're becoming.", "prompt": "It's exactly five years from today. You're reading this letter. Write it now. Tell your future self what you hope they've built, released, healed, or discovered. What do you want them to remember about who you are in this exact moment? And what question do you most want them to be able to answer?"},
    {"theme": "The Apology You Owe Yourself", "tag": "Self-Compassion", "preview": "You've been harder on yourself than you'd be on anyone else.", "prompt": "Think about the last time you were cruel to yourself — through criticism, neglect, or unrealistic standards. Write yourself a genuine apology. Not a performance of self-care, but an honest reckoning. What did you put yourself through? What did you deserve instead? How would you treat a close friend in that same situation?"},
    {"theme": "The Room That Raised You", "tag": "Memory", "preview": "Describe the space where childhood lived.", "prompt": "Close your eyes and walk into the room from your childhood that feels most significant. Describe it in vivid detail — the light, the sounds, the smells, the objects. Who else was there, and what was usually happening? What did that room teach you about safety, love, or belonging? What would you want to go back and change about it?"},
    {"theme": "What You're Quietly Proud Of", "tag": "Self-Worth", "preview": "The wins you never talk about deserve space.", "prompt": "Not the resume-worthy achievements — write about something you've done or become that you're privately proud of but rarely mention. Maybe it's a small habit, a hard conversation you had, something you chose NOT to do. Why haven't you let yourself celebrate it? What would it feel like to fully own it?"},
    {"theme": "The Friendship Audit", "tag": "Relationships", "preview": "Not every relationship deserves equal energy.", "prompt": "Think about the five people you spend the most time with — in person or in your head. For each one, honestly ask: do I feel more like myself or less like myself around them? Do they challenge you, drain you, or hold space for you? What would a truly nourishing friendship look like — and who in your life comes closest to that?"},
    {"theme": "The Thing You Keep Starting Over", "tag": "Patterns", "preview": "Why does this keep happening again?", "prompt": "There's probably something in your life — a habit, a project, a relationship pattern — where you find yourself back at square one repeatedly. Write about it without judgment. What does the beginning always feel like? Where does it usually fall apart? What do you tell yourself each time you restart? And — honestly — what would it actually take to go the distance?"},
    {"theme": "A Conversation With Fear", "tag": "Inner Work", "preview": "Let fear sit down and speak.", "prompt": "Write a dialogue between you and your fear. Give fear a voice — let it say what it's actually afraid of, without you cutting it off. Then respond from your most grounded self. Not to dismiss the fear, but to understand it. What is it protecting you from? Is that threat still real? What would you do if fear wasn't the loudest voice in the room?"},
    {"theme": "The Day That Broke You Open", "tag": "Growth", "preview": "Some of your best growth started as wreckage.", "prompt": "Think of a time when something ended, failed, or collapsed — and eventually you were better for it. Describe what it felt like in the worst moment. Who were you then? Who were you forced to become? Looking back, what's the one thing that experience cracked open in you that might never have opened otherwise?"},
    {"theme": "Your Relationship With Time", "tag": "Mindfulness", "preview": "Do you live in the past, present, or future?", "prompt": "Where does your mind spend most of its time — replaying the past, planning the future, or actually inhabiting the present? Write about a recent day and notice where your attention was. What are you afraid would happen if you were fully here, right now, without plans or memories? What would you actually feel?"},
    {"theme": "The Lie You Tell Most Often", "tag": "Honesty", "preview": "Not to others — to yourself.", "prompt": "We all have a story we tell ourselves to feel okay. What's yours? Maybe it's 'I'm fine,' or 'I'll start when things calm down,' or 'I don't care what people think.' Write about where that story comes from, what it protects you from, and what might be true instead. What's the version of your life that becomes possible when you stop telling it?"},
    {"theme": "The Body Check-In", "tag": "Somatic", "preview": "Your body has been keeping score.", "prompt": "Sit quietly for a moment and do a slow scan from head to toe. Write about what you notice — without trying to fix anything. Where is there tension, numbness, warmth, or weight? When did you last truly listen to what your body was asking for? What has it been trying to tell you this month that you've been too busy to hear?"},
    {"theme": "The Version of You Everyone Sees", "tag": "Authenticity", "preview": "Persona vs. person — how big is the gap?", "prompt": "Think about the 'you' that most people interact with — at work, on social media, at social gatherings. How much does that version match who you actually are when you're alone? What parts of yourself do you edit out, and why? What would happen if you let more of the real you show up? Who in your life already sees the fuller picture?"},
    {"theme": "What Boredom Is Trying To Tell You", "tag": "Curiosity", "preview": "Boredom is rarely just about having nothing to do.", "prompt": "Think of the last time you felt genuinely bored or restless. What were you actually wanting? Connection? Meaning? Stimulation? Escape? Write about what boredom usually signals for you. Is it the absence of something, or the presence of something you're avoiding? What does your restlessness point toward that you haven't yet taken seriously?"},
    {"theme": "The Grudge You're Still Holding", "tag": "Release", "preview": "Holding on feels safer. But is it?", "prompt": "Think of someone you haven't fully forgiven — maybe you've told yourself you have, but there's still a flicker. Write about what happened, from your truest perspective. What did you lose? What do you wish they understood? Then — not for them, but for you — write one sentence that begins: 'I'm choosing to release this because…' You don't have to mean it fully yet. Just write it."},
    {"theme": "Your Dream That Got Shelved", "tag": "Dreams", "preview": "What did you quietly give up on?", "prompt": "There's probably something you wanted — a career, a creative life, a place you wanted to live, a version of yourself — that you quietly set down somewhere along the way. Write about it. When did it start to fade? Was it a decision or a drift? If you were to pick it back up today — even in a small way — what would the first step actually look like?"},
    {"theme": "The Words That Shaped You", "tag": "Language & Identity", "preview": "Something someone said is still living in you.", "prompt": "What is something someone said to you — a parent, teacher, stranger, partner — that you've never fully forgotten? Write the words exactly as you remember them, and then write about what they did to you. Did they build you up or quietly diminish you? Are you still living by those words — and do you want to be? What would you say back now?"},
    {"theme": "A Letter to the Hardest Year", "tag": "Resilience", "preview": "Acknowledge the year that asked the most of you.", "prompt": "Think of the hardest year of your life. Write it a letter. Not a thank-you note — be honest about what it took from you. What you lost, what you had to do just to get through it. Then, if you can, write one thing — however small — that you found in yourself during that time that you didn't know was there. What did survival teach you about your own strength?"},
    {"theme": "The Conversation You Keep Rehearsing", "tag": "Communication", "preview": "You've had it a hundred times in your head.", "prompt": "There's a conversation you've been preparing, postponing, or replaying. Write it out — exactly as you'd want it to go. What do you need to say? What response are you hoping for? What are you afraid of hearing? And then the harder question: what's actually stopping you from having this conversation in real life?"},
    {"theme": "How You Handle Being Wrong", "tag": "Ego & Humility", "preview": "Being wrong is one of the most revealing things about us.", "prompt": "Think of a recent time you were wrong — about a person, a decision, a belief. Write about what happened inside you when you realized it. Did you defend yourself? Go quiet? Overcorrect with guilt? What does being wrong feel like in your body? And what would it look like to handle being wrong with more grace — not self-flagellation, just honest acknowledgment?"},
    {"theme": "The Unfinished Thing", "tag": "Completion", "preview": "What's sitting in the back of your mind, waiting?", "prompt": "Almost everyone has something unfinished that quietly nags — a creative project, a difficult conversation, an unanswered email, an old wound. Write about yours. Why hasn't it been completed? What would it cost you to finish it? What would it give you? Sometimes we keep things unfinished because finishing means something — write about what it would mean for you."},
    {"theme": "Your Relationship With Money", "tag": "Inner Life", "preview": "Money is never just about money.", "prompt": "What did money mean in the home you grew up in? Was it fought over, never discussed, a source of shame or pride? Write about the emotional weight money carries for you now. When you spend, save, or struggle financially — what feelings come with it? What is money really standing in for in your life — security, freedom, worth, love?"},
    {"theme": "The Permission You're Waiting For", "tag": "Agency", "preview": "Who are you waiting to say it's okay?", "prompt": "There's something you want to do — change directions, create something, rest, speak up, leave, begin — and you're waiting for some kind of permission. Write about what you're waiting for and who you imagine needs to give it. What would they have to say? And then write yourself the permission slip, in your own words, signed and dated. What do you actually have permission to do right now?"},
    {"theme": "What Loneliness Feels Like for You", "tag": "Connection", "preview": "Loneliness isn't always about being alone.", "prompt": "Loneliness is different for everyone. Some people feel it most in crowded rooms. Others feel it in relationships. Write about your specific flavor of loneliness. When does it show up? What does it feel like — a heaviness, a hollow, a restlessness? What have you tried to fill it with? And what kind of connection would actually reach it?"},
    {"theme": "The Standard You Can't Let Go Of", "tag": "Perfectionism", "preview": "Some expectations are quietly exhausting you.", "prompt": "Where in your life are you holding yourself to a standard that no longer makes sense — or maybe never did? Write about the rule, the expectation, the bar you keep raising. Where did it come from? What are you afraid would happen if you lowered it? What would 'good enough' actually look like — and could you live with that?"},
    {"theme": "A Moment of Pure Presence", "tag": "Gratitude", "preview": "When were you completely, fully here?", "prompt": "Think of a recent moment — however ordinary — when you were completely present. Not scrolling, not planning, not performing. Just there. Describe it in full sensory detail. What made presence possible in that moment? What would it take to create more of those moments? And what is one thing, right now, that you can be quietly grateful for?"},
    {"theme": "The Belief You Inherited", "tag": "Deconstruction", "preview": "Not all the ideas in your head are yours.", "prompt": "We absorb beliefs about work, love, success, religion, gender, and worth long before we can choose them. Write about one belief you grew up with that you've never fully examined. Where did it come from? How has it shaped your choices? Do you actually believe it — or have you just been living as if you do? What would change if you set it down?"},
    {"theme": "The Eulogy You'd Want", "tag": "Legacy", "preview": "How do you want to have lived?", "prompt": "Imagine your own memorial, years from now. The person who knew you best is speaking. Write the eulogy you would actually want them to give — not the impressive one, the true one. What do you hope they say about how you made people feel? What do you want to have stood for? And the harder question: are you living in a way that makes that eulogy possible right now?"},
    {"theme": "The Thank You Letter", "tag": "Closing", "preview": "End with gratitude — to yourself.", "prompt": "You've made it 30 days. That took something. Write a thank-you letter — to yourself. Thank yourself for showing up. For the days it felt pointless. For the entries you almost didn't write. Acknowledge what you've noticed, uncovered, or released this month. What's different about the person writing this letter versus the one who started on Day 1? What do you want to carry forward?"},
]

MOODS = {
    "reflective": "🤔 Reflective",
    "hopeful":    "🌱 Hopeful",
    "heavy":      "🌧️ Heavy",
    "grateful":   "✨ Grateful",
    "unsettled":  "🌊 Unsettled",
    "peaceful":   "🕊️ Peaceful",
}

# ── DB ────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    client = MongoClient(MONGO_URI)
    db = client.get_default_database() if "/" in MONGO_URI.split("@")[-1] else client["journal30"]
    db.users.create_index("email", unique=True)
    db.entries.create_index([("user_id", ASCENDING), ("day", ASCENDING)], unique=True)
    return db

db = get_db()

# ── Auth helpers ──────────────────────────────────────────────────────────────
def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def check_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def make_token(user_id: str) -> str:
    payload = {"id": user_id, "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRY)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None

def get_current_user():
    token = st.session_state.get("token")
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user = db.users.find_one({"_id": __import__("bson").ObjectId(payload["id"])})
    return user

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── global reset & tokens ── */
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: #0f0e0e; color: #e8e0d5; }

/* ── sidebar ── */
[data-testid="stSidebar"] {
    background: #161412 !important;
    border-right: 1px solid #2a2520;
}

/* ── buttons ── */
.stButton > button {
    background: #c9a96e !important;
    color: #0f0e0e !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.2rem !important;
    transition: opacity .2s;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* ── inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > textarea,
.stSelectbox > div > div {
    background: #1d1a17 !important;
    border: 1px solid #2e2922 !important;
    border-radius: 8px !important;
    color: #e8e0d5 !important;
}

/* ── card component ── */
.card {
    background: #161412;
    border: 1px solid #2a2520;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.card-done { border-color: #c9a96e55; background: #1a1710; }
.card-draft { border-color: #4a8c6055; }

/* ── day grid ── */
.day-grid { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1rem 0; }
.day-cell {
    width: 44px; height: 44px;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: .85rem; font-weight: 600;
    background: #1d1a17; color: #7a6f5e;
    border: 1px solid #2a2520;
}
.day-cell.done  { background: #c9a96e22; color: #c9a96e; border-color: #c9a96e55; }
.day-cell.draft { background: #4a8c6022; color: #7ab890; border-color: #4a8c6055; }

/* ── stat pills ── */
.stat-row { display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0; }
.stat-pill {
    background: #1d1a17; border: 1px solid #2a2520;
    border-radius: 12px; padding: 0.8rem 1.4rem;
    text-align: center; min-width: 100px;
}
.stat-num { font-family: 'DM Serif Display', serif; font-size: 2rem; color: #c9a96e; display: block; }
.stat-label { font-size: .75rem; color: #7a6f5e; text-transform: uppercase; letter-spacing: .08em; }

/* ── prompt box ── */
.prompt-box {
    background: #1a1710; border-left: 3px solid #c9a96e;
    border-radius: 0 8px 8px 0; padding: 1.2rem 1.4rem;
    font-size: 1rem; line-height: 1.7; color: #cfc4b0; margin: 1rem 0;
}

/* ── mood chips ── */
.mood-row { display: flex; flex-wrap: wrap; gap: .5rem; margin: .5rem 0; }

/* ── progress bar ── */
.prog-wrap { background: #1d1a17; border-radius: 99px; height: 8px; margin: .5rem 0; overflow: hidden; }
.prog-fill { height: 100%; background: linear-gradient(90deg, #c9a96e, #e8c98a); border-radius: 99px; transition: width .6s ease; }

/* ── tag badge ── */
.tag { font-size: .72rem; background: #c9a96e22; color: #c9a96e;
       border: 1px solid #c9a96e44; border-radius: 99px; padding: 2px 10px;
       display: inline-block; font-weight: 500; letter-spacing:.05em; }

/* ── heatmap legend ── */
.legend { display: flex; gap: 1.2rem; font-size: .78rem; color: #7a6f5e; margin-top: .8rem; align-items: center; }
.leg-dot { width: 12px; height: 12px; border-radius: 3px; display: inline-block; margin-right: 4px; }

/* ── serif headings ── */
h1, h2, h3 { font-family: 'DM Serif Display', serif !important; }
em { color: #c9a96e; }

/* hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "active_day" not in st.session_state:
    st.session_state.active_day = None

# ── Helper: word count ────────────────────────────────────────────────────────
def word_count(text: str) -> int:
    return len(text.strip().split()) if text.strip() else 0

# ── DB helpers ────────────────────────────────────────────────────────────────
def get_entries(user_id) -> dict:
    docs = db.entries.find({"user_id": str(user_id)})
    return {d["day"]: d for d in docs}

def get_stats(user_id) -> dict:
    entries = list(db.entries.find({"user_id": str(user_id)}))
    completed = [e for e in entries if e.get("completed")]
    total_words = sum(e.get("word_count", 0) for e in entries)
    completed_days = {e["day"] for e in completed}
    streak = 0
    for d in range(1, 31):
        if d in completed_days:
            streak += 1
        else:
            break
    return {
        "total_completed": len(completed),
        "total_words": total_words,
        "streak": streak,
        "completed_days": list(completed_days),
    }

def save_entry(user_id, day: int, content: str, mood: str, completed: bool):
    wc = word_count(content)
    update = {
        "content": content,
        "mood": mood,
        "word_count": wc,
        "updated_at": datetime.utcnow(),
    }
    if completed:
        update["completed"] = True
        update["completed_at"] = datetime.utcnow()
    db.entries.update_one(
        {"user_id": str(user_id), "day": day},
        {"$set": update},
        upsert=True,
    )

def unmark_complete(user_id, day: int):
    db.entries.update_one(
        {"user_id": str(user_id), "day": day},
        {"$set": {"completed": False, "completed_at": None}},
    )

# ── Auth page ─────────────────────────────────────────────────────────────────
def render_auth():
    col1, col2 = st.columns([1.1, 1], gap="large")

    with col1:
        st.markdown("""
        <div style="padding: 2rem 0">
            <div class="tag">✦ 30-Day Challenge</div>
            <h1 style="font-size:3rem; margin:.6rem 0; line-height:1.1">
                Write Your<br><em>Inner World</em>
            </h1>
            <p style="color:#7a6f5e; font-size:1.05rem; margin-bottom:2rem">
                One honest prompt a day. Thirty days of reflection.
            </p>
            <ul style="list-style:none; padding:0; color:#cfc4b0; line-height:2">
                <li>✦ 30 unique daily prompts</li>
                <li>✦ Track your writing streak</li>
                <li>✦ Private, secure entries</li>
                <li>✦ See your growth over time</li>
            </ul>
            <blockquote style="border-left:3px solid #c9a96e; margin:2rem 0; padding-left:1rem; color:#7a6f5e; font-style:italic">
                "The unexamined life is not worth living." — Socrates
            </blockquote>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="your@email.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Sign In →", use_container_width=True)
                if submitted:
                    user = db.users.find_one({"email": email.lower().strip()})
                    if user and check_password(password, user["password"]):
                        st.session_state.token = make_token(str(user["_id"]))
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

        with tab_register:
            with st.form("register_form"):
                name = st.text_input("Your Name", placeholder="How should we call you?")
                email = st.text_input("Email", placeholder="your@email.com", key="reg_email")
                password = st.text_input("Password", type="password", placeholder="At least 6 characters", key="reg_pw")
                submitted = st.form_submit_button("Start the Challenge →", use_container_width=True)
                if submitted:
                    if not name.strip():
                        st.error("Please enter your name.")
                    elif not re.match(r"^\S+@\S+\.\S+$", email):
                        st.error("Please enter a valid email.")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        try:
                            result = db.users.insert_one({
                                "name": name.strip(),
                                "email": email.lower().strip(),
                                "password": hash_password(password),
                                "challenge_start_date": datetime.utcnow(),
                                "created_at": datetime.utcnow(),
                            })
                            st.session_state.token = make_token(str(result.inserted_id))
                            st.rerun()
                        except DuplicateKeyError:
                            st.error("An account with this email already exists.")

# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar(user, entries, stats):
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:.5rem 0 1rem">
            <div class="tag">✦ 30-Day Challenge</div>
            <h2 style="margin:.5rem 0 0; font-size:1.4rem">
                Write Your <em>Inner World</em>
            </h2>
            <p style="color:#7a6f5e; font-size:.85rem; margin:.3rem 0 1rem">
                Welcome back, {user['name'].split()[0]}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Progress bar
        pct = (stats["total_completed"] / 30) * 100
        st.markdown(f"""
        <div style="margin-bottom:1.2rem">
            <div style="display:flex;justify-content:space-between;font-size:.78rem;color:#7a6f5e;margin-bottom:.3rem">
                <span>Progress</span><span>{stats['total_completed']} / 30</span>
            </div>
            <div class="prog-wrap"><div class="prog-fill" style="width:{pct}%"></div></div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("📖 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        if st.button("📊 Stats", use_container_width=True):
            st.session_state.page = "stats"
            st.rerun()

        st.markdown("---")
        st.markdown("<p style='font-size:.75rem;color:#7a6f5e;margin-bottom:.5rem'>YOUR DAYS</p>", unsafe_allow_html=True)

        # Mini day list
        for i, p in enumerate(PROMPTS):
            day = i + 1
            e = entries.get(day)
            icon = "✓ " if e and e.get("completed") else ("· " if e and e.get("content") else "  ")
            color = "#c9a96e" if e and e.get("completed") else ("#7ab890" if e and e.get("content") else "#7a6f5e")
            if st.button(
                f"{icon}Day {day}: {p['theme'][:22]}{'…' if len(p['theme']) > 22 else ''}",
                key=f"nav_{day}",
                use_container_width=True,
            ):
                st.session_state.page = "entry"
                st.session_state.active_day = day
                st.rerun()

        st.markdown("---")
        if st.button("Sign Out", use_container_width=True):
            st.session_state.token = None
            st.session_state.page = "dashboard"
            st.rerun()

# ── Dashboard ─────────────────────────────────────────────────────────────────
def render_dashboard(user, entries, stats):
    st.markdown(f"""
    <div style="margin-bottom:1.5rem">
        <div class="tag">✦ 30-Day Challenge</div>
        <h1 style="font-size:2.8rem; margin:.4rem 0; line-height:1.1">
            Write Your<br><em>Inner World</em>
        </h1>
        <p style="color:#7a6f5e">One prompt a day. Thirty days of honest reflection.</p>
    </div>
    """, unsafe_allow_html=True)

    # Stats row
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-pill">
            <span class="stat-num">{stats['total_completed']}</span>
            <span class="stat-label">Days Done</span>
        </div>
        <div class="stat-pill">
            <span class="stat-num">{stats['streak']}</span>
            <span class="stat-label">Day Streak</span>
        </div>
        <div class="stat-pill">
            <span class="stat-num">{stats['total_words']:,}</span>
            <span class="stat-label">Words Written</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### All 30 Days")

    # 3-column card grid
    cols = st.columns(3)
    for i, p in enumerate(PROMPTS):
        day = i + 1
        e = entries.get(day)
        is_done  = e and e.get("completed")
        has_draft = e and e.get("content") and not is_done
        card_class = "card-done" if is_done else ("card-draft" if has_draft else "")
        wc = e.get("word_count", 0) if e else 0
        mood_label = MOODS.get(e.get("mood", ""), "") if e else ""

        with cols[i % 3]:
            st.markdown(f"""
            <div class="card {card_class}" style="min-height:130px">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div class="tag">{p['tag']}</div>
                    <span style="font-size:.75rem;color:{'#c9a96e' if is_done else '#7a6f5e'}">
                        {'✓ Done' if is_done else (f'✍ {wc}w' if has_draft else f'Day {day}')}
                    </span>
                </div>
                <div style="font-family:'DM Serif Display',serif;font-size:1.1rem;margin:.5rem 0 .3rem;color:#e8e0d5">
                    {p['theme']}
                </div>
                <div style="font-size:.82rem;color:#7a6f5e">{p['preview']}</div>
                {f'<div style="font-size:.8rem;color:#7a6f5e;margin-top:.4rem">{mood_label}</div>' if mood_label else ''}
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"{'Review' if is_done else 'Write'} Day {day}", key=f"dash_{day}", use_container_width=True):
                st.session_state.page = "entry"
                st.session_state.active_day = day
                st.rerun()

# ── Entry page ────────────────────────────────────────────────────────────────
def render_entry(user, entries):
    day = st.session_state.active_day
    if not day or day < 1 or day > 30:
        st.error("Invalid day.")
        return

    p = PROMPTS[day - 1]
    e = entries.get(day, {})
    is_done = e.get("completed", False)

    # Back button
    col_back, col_nav = st.columns([1, 3])
    with col_back:
        if st.button("← All Days"):
            st.session_state.page = "dashboard"
            st.rerun()

    # Header
    st.markdown(f"""
    <div style="margin:1rem 0 .5rem">
        <span style="font-size:.85rem;color:#7a6f5e">Day {day} of 30</span>
        <h1 style="font-size:2.2rem;margin:.2rem 0">{p['theme']}</h1>
        <div class="tag">{p['tag']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Prompt box
    st.markdown(f'<div class="prompt-box">{p["prompt"]}</div>', unsafe_allow_html=True)

    # Mood picker
    st.markdown("**How are you feeling right now?**")
    current_mood = e.get("mood", "")
    mood_cols = st.columns(len(MOODS))
    new_mood = current_mood
    for idx, (mv, ml) in enumerate(MOODS.items()):
        with mood_cols[idx]:
            selected = current_mood == mv
            label = f"{'✓ ' if selected else ''}{ml}"
            if st.button(label, key=f"mood_{mv}", use_container_width=True):
                new_mood = "" if selected else mv

    st.markdown("---")

    # Editor
    col_label, col_status = st.columns([3, 1])
    with col_label:
        st.markdown("**Your Reflection**")
    with col_status:
        if is_done:
            st.markdown("<span style='color:#c9a96e'>✓ Completed</span>", unsafe_allow_html=True)

    content = st.text_area(
        "Write here",
        value=e.get("content", ""),
        height=320,
        placeholder="Start writing… there's no wrong answer here. The only rule is honesty.",
        disabled=is_done,
        label_visibility="collapsed",
        key=f"editor_{day}",
    )

    wc = word_count(content)
    st.caption(f"{wc} {'word' if wc == 1 else 'words'}")

    # Actions
    col_save, col_complete, col_unmark = st.columns([1, 1, 1])

    with col_save:
        if not is_done:
            if st.button("💾 Save Draft", use_container_width=True):
                save_entry(str(user["_id"]), day, content, new_mood, False)
                st.success("Saved!")
                st.rerun()

    with col_complete:
        if not is_done:
            if st.button("✓ Mark Complete", use_container_width=True, disabled=not content.strip()):
                save_entry(str(user["_id"]), day, content, new_mood, True)
                st.success(f"🎉 Day {day} complete!")
                st.rerun()
        else:
            st.markdown(f"<div style='text-align:center;color:#c9a96e;padding:.5rem'>🎉 Day {day} done!</div>", unsafe_allow_html=True)

    with col_unmark:
        if is_done:
            if st.button("↩ Reopen", use_container_width=True):
                unmark_complete(str(user["_id"]), day)
                st.rerun()

    # Mood update if changed
    if new_mood != current_mood and not is_done:
        save_entry(str(user["_id"]), day, content, new_mood, False)
        st.rerun()

    # Day navigation
    st.markdown("---")
    nav_l, nav_r = st.columns(2)
    with nav_l:
        if day > 1:
            if st.button(f"← Day {day - 1}", use_container_width=True):
                st.session_state.active_day = day - 1
                st.rerun()
    with nav_r:
        if day < 30:
            if st.button(f"Day {day + 1} →", use_container_width=True):
                st.session_state.active_day = day + 1
                st.rerun()

# ── Stats page ────────────────────────────────────────────────────────────────
def render_stats(user, entries, stats):
    st.markdown("<h1>Your <em>Progress</em></h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#7a6f5e'>A reflection on your 30-day journey so far.</p>", unsafe_allow_html=True)

    # Big stats
    avg_words = round(stats["total_words"] / stats["total_completed"]) if stats["total_completed"] else 0
    col1, col2, col3, col4 = st.columns(4)
    for col, num, label, sub in [
        (col1, stats["total_completed"], "Days Completed", "out of 30"),
        (col2, stats["streak"], "Current Streak", "consecutive days"),
        (col3, f"{stats['total_words']:,}", "Words Written", "total"),
        (col4, avg_words, "Avg Words / Entry", "per completed day"),
    ]:
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center">
                <div class="stat-num">{num}</div>
                <div style="font-weight:600;color:#cfc4b0;font-size:.9rem">{label}</div>
                <div style="font-size:.75rem;color:#7a6f5e">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    # Insights
    mood_counts: dict = {}
    for e in entries.values():
        if e.get("mood"):
            mood_counts[e["mood"]] = mood_counts.get(e["mood"], 0) + 1

    if mood_counts:
        top_mood_key = max(mood_counts, key=mood_counts.get)
        top_mood_label = MOODS[top_mood_key]
        longest = max(entries.values(), key=lambda x: x.get("word_count", 0), default=None)

        st.markdown("### Insights")
        ic1, ic2 = st.columns(2)
        with ic1:
            st.markdown(f"""
            <div class="card">
                <div style="font-size:1.8rem">{top_mood_label.split()[0]}</div>
                <strong>Most frequent mood</strong><br>
                <span style="color:#7a6f5e">{' '.join(top_mood_label.split()[1:])} ({mood_counts[top_mood_key]}×)</span>
            </div>
            """, unsafe_allow_html=True)
        if longest:
            with ic2:
                theme = PROMPTS[longest["day"] - 1]["theme"]
                st.markdown(f"""
                <div class="card">
                    <div style="font-size:1.8rem">✍️</div>
                    <strong>Longest entry</strong><br>
                    <span style="color:#7a6f5e">Day {longest['day']}: {theme} — {longest.get('word_count',0)} words</span>
                </div>
                """, unsafe_allow_html=True)

    if stats["total_completed"] == 30:
        st.success("🏆 Challenge Complete! You finished all 30 days. That's extraordinary.")

    # Heatmap
    st.markdown("### 30-Day Overview")
    completed_set = set(stats["completed_days"])
    draft_set = {d for d, e in entries.items() if e.get("content") and d not in completed_set}

    cells = ""
    for i in range(30):
        d = i + 1
        cls = "done" if d in completed_set else ("draft" if d in draft_set else "")
        cells += f'<div class="day-cell {cls}" title="Day {d}">{d}</div>'

    st.markdown(f"""
    <div class="day-grid">{cells}</div>
    <div class="legend">
        <span><span class="leg-dot" style="background:#1d1a17;border:1px solid #2a2520"></span> Not started</span>
        <span><span class="leg-dot" style="background:#4a8c6022;border:1px solid #4a8c6055"></span> In progress</span>
        <span><span class="leg-dot" style="background:#c9a96e22;border:1px solid #c9a96e55"></span> Complete</span>
    </div>
    """, unsafe_allow_html=True)

    # Completed list
    completed_entries = sorted(
        [e for e in entries.values() if e.get("completed")],
        key=lambda x: x["day"]
    )
    if completed_entries:
        st.markdown("### Completed Days")
        for e in completed_entries:
            day = e["day"]
            theme = PROMPTS[day - 1]["theme"]
            mood_label = MOODS.get(e.get("mood", ""), "")
            col_info, col_open = st.columns([5, 1])
            with col_info:
                st.markdown(f"""
                <div class="card card-done" style="padding:.8rem 1rem;margin:.3rem 0">
                    <span style="color:#c9a96e;font-weight:600">Day {day}</span>
                    <span style="color:#cfc4b0;margin-left:.6rem">{theme}</span>
                    <span style="color:#7a6f5e;font-size:.8rem;margin-left:1rem">
                        {mood_label} · {e.get('word_count',0)} words
                    </span>
                </div>
                """, unsafe_allow_html=True)
            with col_open:
                if st.button("Open", key=f"stats_open_{day}"):
                    st.session_state.page = "entry"
                    st.session_state.active_day = day
                    st.rerun()

    if stats["total_completed"] == 0:
        st.info("You haven't completed any days yet. Head to the dashboard to start!")
        if st.button("Start Day 1 →"):
            st.session_state.page = "entry"
            st.session_state.active_day = 1
            st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    user = get_current_user()

    if not user:
        render_auth()
        return

    entries = get_entries(user["_id"])
    stats   = get_stats(user["_id"])

    render_sidebar(user, entries, stats)

    page = st.session_state.page
    if page == "dashboard":
        render_dashboard(user, entries, stats)
    elif page == "entry":
        render_entry(user, entries)
    elif page == "stats":
        render_stats(user, entries, stats)

if __name__ == "__main__":
    main()
