import streamlit as st
import PyPDF2
import re

# Define target skills and roles
TARGET_SKILLS = ["python", "pyspark", "sql", "aws", "ai", "machine learning", "deep learning", "cloud"]

ROLES = {
    "Data Engineer": ["python", "pyspark", "sql", "aws"],
    "AI/ML Engineer": ["python", "ai", "machine learning", "deep learning", "sql"],
    "Cloud Architect": ["aws", "python", "cloud"],
    "Data Analyst": ["sql", "python"],
    "Big Data Developer": ["pyspark", "python", "sql", "aws"]
}

# --- Chatbot Logic ---
def get_chatbot_response(user_input, found_skills=None):
    user_input = user_input.lower()
    
    # Check for Data Engineer role questions
    if "data engineer" in user_input:
        missing = set(ROLES["Data Engineer"]) - (found_skills or set())
        if missing:
            skills_str = ", ".join([s.title() for s in missing])
            return f"To become a Data Engineer, you still need to focus on: **{skills_str}**.\n\nHere are some great resources:\n- **Python:** [Corey Schafer's Python Playlist](https://www.youtube.com/playlist?list=PL-osiE80TeTt2d9bfVyTiXJA-UTHn6WwU)\n- **SQL:** [SQLTutorial.org](https://www.sqltutorial.org/) or Mode Analytics SQL Tutorial\n- **PySpark:** [DataBricks PySpark Guide](https://spark.apache.org/docs/latest/api/python/getting_started/index.html) or FreeCodeCamp YouTube\n- **AWS:** [AWS Skill Builder](https://skillbuilder.aws/) (Free Tier)"
        else:
            return "You already have the core skills for a Data Engineer! You should focus on building complex data pipeline projects and preparing for interviews. Check out resources like LeetCode for SQL and Python."
            
    # Check for general skill learning questions
    elif "python" in user_input:
        return "For **Python**, I highly recommend:\n1. **YouTube:** Programming with Mosh or Corey Schafer\n2. **Websites:** [RealPython.com](https://realpython.com) or [FreeCodeCamp](https://www.freecodecamp.org/)\n3. **Practice:** HackerRank or LeetCode."
    elif "sql" in user_input:
        return "For **SQL**, check out:\n1. **Websites:** [SQLBolt](https://sqlbolt.com/) (Interactive) or [W3Schools](https://www.w3schools.com/sql/)\n2. **YouTube:** Joey Blue or Kudvenkat SQL Server tutorials\n3. **Practice:** StrataScratch (Great for Data roles)."
    elif "pyspark" in user_input or "spark" in user_input:
        return "For **PySpark**, check out:\n1. **YouTube:** Krish Naik's PySpark playlist or FreeCodeCamp's Apache Spark tutorial.\n2. **Documentation:** The official Apache Spark documentation is excellent for beginners."
    elif "aws" in user_input or "cloud" in user_input:
        return "For **AWS / Cloud**, check out:\n1. **YouTube:** Stephane Maarek (for certification prep) or freeCodeCamp's AWS Practitioner course.\n2. **Websites:** AWS Skill Builder (official and free) or A Cloud Guru."
    elif "ai" in user_input or "machine learning" in user_input:
        return "For **AI & Machine Learning**, I recommend:\n1. **Courses:** Andrew Ng's Machine Learning Specialization on Coursera.\n2. **YouTube:** StatQuest with Josh Starmer or Sentdex (for Python ML).\n3. **Websites:** Kaggle (for datasets and notebooks)."
    
    # Generic fallback
    return "That's a great question! Based on your profile, focusing on Python, SQL, and Cloud (AWS) is always a safe bet for Data/AI roles. Try searching on YouTube for 'FreeCodeCamp [Skill Name]' for high-quality, free tutorials!"

# --- Main App ---
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

st.title("📄 AI-Powered Resume Analyzer & Career Coach")
st.markdown("Upload your resume to discover suitable roles, identify skills to improve, and chat with our AI coach for learning resources!")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "found_skills" not in st.session_state:
    st.session_state.found_skills = set()

st.sidebar.header("Upload Section")
uploaded_file = st.sidebar.file_uploader("Upload Resume (PDF)", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Analyzing your resume..."):
        text = extract_text_from_pdf(uploaded_file)
        
        if not text.strip():
            st.error("Could not extract text from the uploaded PDF. Please try another file.")
        else:
            found_skills = extract_skills(text)
            st.session_state.found_skills = found_skills # Save for the chatbot
            
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
st.subheader("💬 Ask the Career Coach")
st.write("Ask for learning resources or advice (e.g., *'I am not suitable for Data Engineer, what skills should I learn?'*)")

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask about roles or skills..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get bot response (pass the skills we found from the resume)
    response = get_chatbot_response(prompt, st.session_state.found_skills)
    
    # Display bot response
    with st.chat_message("assistant"):
        st.markdown(response)
        
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
