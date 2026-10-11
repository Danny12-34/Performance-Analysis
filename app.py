import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pdf_reader import extract_marks
from analyzer import analyze
from report_generator import generate_pdf

# -------------------------
# PAGE SETUP
# -------------------------
st.set_page_config(page_title="Student Analysis Dashboard", page_icon="📊", layout="wide")

# HERO HEADER
st.markdown("""
<div style="padding:20px;background:linear-gradient(135deg,#1f4e78,#2e86de);color:white;border-radius:12px;">
<h1>📊 Student Performance Analysis Dashboard</h1>
<p>Upload marksheet PDFs and get automatic insights, charts, and downloadable reports.</p>
</div>
""", unsafe_allow_html=True)

# SIDEBAR
st.sidebar.title("⚙️ Upload & Settings")
uploaded_files = st.sidebar.file_uploader("Upload PDF marksheets", type="pdf", accept_multiple_files=True)

# -------------------------
# CLASS, TEACHER, SUBJECT INPUTS
# -------------------------
class_name = st.sidebar.selectbox(
    "Class Name",
    ["S1 A", "S1 B", "S1 C", "S1 D", "S2 A", "S2 B", "S3" , "S4 ACC","S5 ACC","S6 ACC",
     "L3 CSA", "L3 SOD","L3 NIT", "L3 ETE","L3 BUC", "L3 AUT",
     "L4 CSA", "L4 SOD","L4 NIT", "L4 ETE","L4 BUC", "L4 AUT",
     "L5 CSA", "L5 SOD","L5 NIT", "L5 ETE","L5 BUC", "L5 AUT"]
)

teacher_name = st.sidebar.selectbox(
    "Teacher Name",
    ["Teacher Name", "Niyitanga Danny", "Rachel NIYONKUNDA", "Rukundo Jean Damour"]
)

subject_name = st.sidebar.selectbox(
    "Select Subject",
    options=[
        "Select Subject",
        "Apply Python Programming Fundamentals",
        "Develop a Backend Application using Node.js",
        "Develop Frontend Application using React.JS",
        "Develop Mobile Application using Flutter",
        "Develop NoSQL Database",
        "Apply JavaScript",
        "Apply C Programming Fundamentals",
        "Apply C++ Programming",
        "Apply Data Structures and Algorithms using C"
    ]
)

# Dynamic Max Marks inputs for each uploaded file
max_marks = []
if uploaded_files:
    st.sidebar.markdown("### 🎯 Max Marks")
    for file in uploaded_files:
        m = st.sidebar.number_input(f"{file.name}", min_value=1, value=100)
        max_marks.append(m)

# -------------------------
# ANALYZE BUTTON
# -------------------------
if uploaded_files and st.sidebar.button("🚀 Analyze Students"):
    # Extract marks dataframes and format column headers with file name and / Max value
    all_dfs = []
    for i, file in enumerate(uploaded_files):
        df = extract_marks(file)
        m = max_marks[i]
        if "Marks" in df.columns:
            df = df.rename(columns={"Marks": f"{file.name} / {m}"})
        all_dfs.append(df)
    
    # Pass dataframes and max_marks list to analyzer using Method 1 logic
    result = analyze(all_dfs, max_marks)

    # METRICS
    st.subheader("📈 Class Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Class Average", f"{result['Percentage'].mean():.2f}%")
    col2.metric("Total Students", len(result))
    col3.metric("Excellent", len(result[result["Category"]=="Excellent"]))
    col4.metric("Need Help", len(result[result["Category"]=="Weak"]))

    # CHARTS
    st.subheader("📊 Performance Charts")
    c1, c2 = st.columns(2)
    with c1:
        cat_counts = result["Category"].value_counts()
        fig, ax = plt.subplots()
        ax.pie(cat_counts, labels=cat_counts.index, autopct='%1.1f%%')
        ax.set_facecolor("white")
        st.pyplot(fig)
    with c2:
        top10 = result.sort_values("Percentage", ascending=False).head(10)
        st.bar_chart(top10.set_index("Student Name")["Percentage"])

    # RESULTS TABLE
    st.subheader("📋 Student Results")
    st.dataframe(result.sort_values("Percentage", ascending=False), use_container_width=True)

    # WEAK STUDENTS
    st.subheader("⚠ Students Needing Special Help")
    weak_df = result[result["Category"]=="Weak"]
    if len(weak_df) > 0:
        st.dataframe(weak_df[["Student Name", "Percentage"]], use_container_width=True)
    else:
        st.success("No students currently in weak category 🎉")

    # GENERATE & DOWNLOAD REPORTS
    result.to_excel("analysis.xlsx", index=False)
    generate_pdf(result, class_name, subject_name, teacher_name)

    colA, colB = st.columns(2)
    with colA:
        with open("analysis.xlsx", "rb") as f:
            st.download_button("⬇ Download Excel Report", f, "student_analysis.xlsx")
    with colB:
        with open("report.pdf", "rb") as f:
            st.download_button("⬇ Download PDF Report", f, "student_report.pdf")