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
        # Using word boundaries to avoid partial matches
        if re.search(r'\b' + re.escape(skill) + r'\b', text):
            found_skills.add(skill)
    return found_skills

def analyze_roles(found_skills):
    suitable_roles = []
    for role, req_skills in ROLES.items():
        match_count = sum(1 for s in req_skills if s in found_skills)
        match_percentage = match_count / len(req_skills)
        if match_percentage >= 0.2: # At least 20% match to show something
            suitable_roles.append((role, match_percentage))
    
    # Sort by match percentage
    suitable_roles.sort(key=lambda x: x[1], reverse=True)
    return suitable_roles

def get_skills_to_improve(found_skills, role):
    req_skills = set(ROLES[role])
    missing = req_skills - found_skills
    return missing

st.set_page_config(page_title="Resume Analyzer Dashboard", page_icon="📄", layout="wide")

st.title("📄 AI-Powered Resume Analyzer")
st.markdown("Upload your resume to discover suitable roles and identify skills to improve based on industry trends.")

st.sidebar.header("Upload Section")
uploaded_file = st.sidebar.file_uploader("Upload Resume (PDF)", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Analyzing your resume..."):
        text = extract_text_from_pdf(uploaded_file)
        
        if not text.strip():
            st.error("Could not extract text from the uploaded PDF. Please try another file.")
        else:
            found_skills = extract_skills(text)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🛠️ Extracted Skills")
                if found_skills:
                    for skill in found_skills:
                        st.success(skill.title())
                else:
                    st.warning("No target skills found. Make sure to include relevant keywords.")
            
            with col2:
                st.subheader("🎯 Suitable Roles")
                suitable_roles = analyze_roles(found_skills)
                if suitable_roles:
                    for role, match_pct in suitable_roles:
                        st.info(f"**{role}** (Match: {match_pct:.0%})")
                else:
                    st.error("Not enough matching skills for the predefined roles.")
            
            st.markdown("---")
            st.subheader("📈 Skills to Improve")
            if suitable_roles:
                # Show skills to improve for the top matched role
                top_role = suitable_roles[0][0]
                missing_skills = get_skills_to_improve(found_skills, top_role)
                
                st.write(f"To become a better fit for your top role (**{top_role}**), consider learning:")
                if missing_skills:
                    for skill in missing_skills:
                        st.error(skill.title())
                else:
                    st.success("You have all the core skills for this role!")
                    
                st.write("Other core skills to consider across all Data/AI roles:")
                all_core_skills = set(TARGET_SKILLS) - found_skills
                if all_core_skills:
                    st.write(", ".join([s.title() for s in all_core_skills]))
            else:
                st.write("Consider learning some of these core skills to improve your profile:")
                for skill in TARGET_SKILLS:
                    st.write(f"- {skill.title()}")
                    
else:
    st.info("Please upload a PDF resume from the sidebar to begin.")
