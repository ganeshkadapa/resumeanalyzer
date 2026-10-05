import streamlit as st
import PyPDF2
import re
import sqlite3
import hashlib
import google.generativeai as genai

# --- Database & Security Functions ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()
    return conn, c

def create_user(username, password):
    conn, c = init_db()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, make_hashes(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn, c = init_db()
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    
    if data:
        hashed_password = data[0]
        if check_hashes(password, hashed_password):
            return True
    return False

# Initialize session state for authentication
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

init_db()

# --- Resume Analyzer Constants ---
TARGET_SKILLS = ["python", "pyspark", "sql", "aws", "ai", "machine learning", "deep learning", "cloud"]

ROLES = {
    "Data Engineer": ["python", "pyspark", "sql", "aws"],
    "AI/ML Engineer": ["python", "ai", "machine learning", "deep learning", "sql"],
    "Cloud Architect": ["aws", "python", "cloud"],
    "Data Analyst": ["sql", "python"],
    "Big Data Developer": ["pyspark", "python", "sql", "aws"]
}

# --- REAL Generative AI Chatbot Logic ---
def get_chatbot_response(user_input, found_skills, api_key):
    if not api_key:
        return "⚠️ **Please enter your Gemini API Key in the sidebar to activate the AI Career Coach!**"
    
    try:
        genai.configure(api_key=api_key)
        # Using gemini-1.5-flash as it is fast and free
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are an expert AI Career Coach. 
        The user has uploaded their resume and we extracted these core skills: {found_skills}.
        
        The user is asking: "{user_input}"
        
        Provide a helpful, encouraging, and highly specific response. 
        If they ask for resources, suggest actual platforms (like Coursera, freeCodeCamp, Udemy, specific YouTube channels, or Kaggle). 
        Use markdown formatting to make your answer easy to read.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ **Error communicating with Gemini AI:** {str(e)}"

# --- Main App Helpers ---
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + " "
    return text

def extract_skills(text):
    text = text.lower()
    found_skills = set()
    for skill in TARGET_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text):
            found_skills.add(skill)
    return found_skills

def analyze_roles(found_skills):
    suitable_roles = []
    for role, req_skills in ROLES.items():
        match_count = sum(1 for s in req_skills if s in found_skills)
        match_percentage = match_count / len(req_skills)
        if match_percentage >= 0.2:
            suitable_roles.append((role, match_percentage))
    suitable_roles.sort(key=lambda x: x[1], reverse=True)
    return suitable_roles

def get_skills_to_improve(found_skills, role):
    req_skills = set(ROLES[role])
    return req_skills - found_skills

st.set_page_config(page_title="Resume Analyzer Dashboard", page_icon="📄", layout="wide")

# ==========================================
# AUTHENTICATION LOGIC (Login & Sign Up)
# ==========================================
if not st.session_state.logged_in:
    st.title("🔒 Access Dashboard")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login to your account")
        with st.form("login_form"):
            login_username = st.text_input("Username")
            login_password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
            
            if submit_login:
                if login_user(login_username, login_password):
                    st.session_state.logged_in = True
                    st.session_state.username = login_username
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    
    with tab2:
        st.subheader("Create a new account")
        with st.form("signup_form"):
            new_username = st.text_input("Choose a Username")
            new_password = st.text_input("Choose a Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_signup = st.form_submit_button("Sign Up")
            
            if submit_signup:
                if new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif len(new_username) < 3 or len(new_password) < 4:
                    st.error("Username must be at least 3 characters and password at least 4 characters.")
                else:
                    success = create_user(new_username, new_password)
                    if success:
                        st.success("Account created successfully! You can now log in from the Login tab.")
                    else:
                        st.error(f"Username '{new_username}' is already taken. Please choose another one.")
                
else:
    # ==========================================
    # MAIN DASHBOARD (Only visible if logged in)
    # ==========================================
    
    st.sidebar.markdown(f"**Welcome, {st.session_state.username}!**")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.header("🤖 AI Settings")
    api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Paste your Google AI Studio key here to activate the chatbot.")

    st.title("📄 AI-Powered Resume Analyzer & Career Coach")
    st.markdown("Upload your resume to discover suitable roles, identify skills to improve, and chat with our **Generative AI** coach for personalized advice!")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "found_skills" not in st.session_state:
        st.session_state.found_skills = set()

    st.sidebar.markdown("---")
    st.sidebar.header("Upload Section")
    uploaded_file = st.sidebar.file_uploader("Upload Resume (PDF)", type=["pdf"])

    if uploaded_file is not None:
        with st.spinner("Analyzing your resume..."):
            text = extract_text_from_pdf(uploaded_file)
            
            if not text.strip():
                st.error("Could not extract text from the uploaded PDF. Please try another file.")
            else:
                found_skills = extract_skills(text)
                st.session_state.found_skills = found_skills 
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🛠️ Extracted Skills")
                    if found_skills:
                        for skill in found_skills:
                            st.success(skill.title())
                    else:
                        st.warning("No target skills found.")
                
                with col2:
                    st.subheader("🎯 Suitable Roles")
                    suitable_roles = analyze_roles(found_skills)
                    if suitable_roles:
                        for role, match_pct in suitable_roles:
                            st.info(f"**{role}** (Match: {match_pct:.0%})")
                    else:
                        st.error("Not enough matching skills.")
                
                st.markdown("---")
                
    else:
        st.info("Please upload a PDF resume from the sidebar to begin analysis.")

    # --- Chatbot UI ---
    st.markdown("---")
    st.subheader("💬 Ask the Generative AI Career Coach")
    st.write("Ask any career question! (e.g., *'I want to transition from Data Analyst to Data Engineer. What 3 projects should I build?'*)")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask for personalized career advice..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("AI is thinking..."):
            response = get_chatbot_response(prompt, st.session_state.found_skills, api_key)
        
        with st.chat_message("assistant"):
            st.markdown(response)
            
        st.session_state.messages.append({"role": "assistant", "content": response})
