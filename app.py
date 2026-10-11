import io
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pdf_reader import extract_marks
from analyzer import analyze
from report_generator import generate_pdf

# =========================================================
# PAGE SETUP
# =========================================================
st.set_page_config(
    page_title="Student Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Color themes (user can switch in the sidebar)
# ---------------------------------------------------------
THEMES = {
    "🌌 Royal":  {"c1": "#1e3a8a", "c2": "#4f46e5", "c3": "#9333ea", "accent": "#4f46e5", "bg1": "#f4f7ff", "bg2": "#eef2fb"},
    "🌊 Ocean":  {"c1": "#0f4c81", "c2": "#0891b2", "c3": "#14b8a6", "accent": "#0891b2", "bg1": "#f0fbfd", "bg2": "#e6f6f8"},
    "🌅 Sunset": {"c1": "#be123c", "c2": "#f97316", "c3": "#f59e0b", "accent": "#f97316", "bg1": "#fff8f3", "bg2": "#fff1e6"},
    "🌿 Forest": {"c1": "#14532d", "c2": "#16a34a", "c3": "#65a30d", "accent": "#16a34a", "bg1": "#f3fbf4", "bg2": "#e8f6ea"},
}

CATEGORY_COLORS = {
    "Excellent": "#10b981",
    "Good": "#3b82f6",
    "Average": "#f59e0b",
    "Fair": "#f59e0b",
    "Weak": "#ef4444",
}
FALLBACK_COLORS = ["#8b5cf6", "#06b6d4", "#ec4899", "#84cc16"]


def color_for(category, index=0):
    return CATEGORY_COLORS.get(category, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])


# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("⚙️ Upload & Settings")

theme_name = st.sidebar.selectbox("🎨 Color Theme", list(THEMES.keys()))
T = THEMES[theme_name]

uploaded_files = st.sidebar.file_uploader(
    "Upload PDF marksheets", type="pdf", accept_multiple_files=True
)

class_name = st.sidebar.selectbox(
    "🏫 Class Name",
    ["S1 A", "S1 B", "S1 C", "S1 D", "S2 A", "S2 B", "S3", "S4 ACC", "S5 ACC", "S6 ACC",
     "L3 CSA", "L3 SOD", "L3 NIT", "L3 ETE", "L3 BUC", "L3 AUT",
     "L4 CSA", "L4 SOD", "L4 NIT", "L4 ETE", "L4 BUC", "L4 AUT",
     "L5 CSA", "L5 SOD", "L5 NIT", "L5 ETE", "L5 BUC", "L5 AUT"],
)

teacher_name = st.sidebar.selectbox(
    "👨‍🏫 Teacher Name",
    ["Teacher Name", "Niyitanga Danny", "Rachel NIYONKUNDA", "Rukundo Jean Damour"],
)

subject_name = st.sidebar.selectbox(
    "📘 Select Subject",
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
        "Apply Data Structures and Algorithms using C",
    ],
)

pass_mark = st.sidebar.slider("✅ Pass mark (%)", 0, 100, 50, help="Used for pass rate and at-risk detection.")

max_marks = []
if uploaded_files:
    st.sidebar.markdown("### 🎯 Max Marks")
    for idx, file in enumerate(uploaded_files):
        m = st.sidebar.number_input(
            f"{file.name}", min_value=1, value=100, key=f"max_{idx}_{file.name}"
        )
        max_marks.append(m)

analyze_clicked = st.sidebar.button("🚀 Analyze Students")

# =========================================================
# GLOBAL CSS (themed)
# =========================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

.stApp { background: linear-gradient(180deg, %%BG1%% 0%, %%BG2%% 100%); }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.5rem; padding-bottom: 5rem; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, %%BG2%% 0%, #f3e8ff 100%);
    border-right: 1px solid rgba(0,0,0,0.06);
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: %%C1%%; }

.hero {
    padding: 32px 36px;
    background: linear-gradient(135deg, %%C1%% 0%, %%C2%% 55%, %%C3%% 100%);
    color: white; border-radius: 20px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.20);
    margin-bottom: 26px; position: relative; overflow: hidden;
}
.hero::after {
    content: ""; position: absolute; right: -60px; top: -60px;
    width: 240px; height: 240px; background: rgba(255,255,255,0.10); border-radius: 50%;
}
.hero::before {
    content: ""; position: absolute; right: 120px; bottom: -90px;
    width: 180px; height: 180px; background: rgba(255,255,255,0.07); border-radius: 50%;
}
.hero h1 { margin: 0 0 6px 0; font-size: 2.1rem; font-weight: 700; }
.hero p  { margin: 0; font-size: 1.05rem; opacity: .92; }
.hero .chip {
    display: inline-block; margin: 14px 8px 0 0; padding: 5px 14px;
    background: rgba(255,255,255,0.18); border-radius: 999px; font-size: .85rem;
}

.section-title {
    font-size: 1.2rem; font-weight: 600; color: %%C1%%;
    margin: 22px 0 12px 0; padding-left: 12px; border-left: 5px solid %%ACCENT%%;
}

.kpi {
    background: white; border-radius: 16px; padding: 18px 20px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.07);
    border-top: 5px solid var(--accent);
    transition: transform .2s ease, box-shadow .2s ease; height: 100%;
}
.kpi:hover { transform: translateY(-4px); box-shadow: 0 12px 26px rgba(0,0,0,0.14); }
.kpi .icon  { font-size: 1.5rem; }
.kpi .value { color: var(--accent); font-size: 1.8rem; font-weight: 700; line-height: 1.2; }
.kpi .label { color: #64748b; font-size: .82rem; font-weight: 500; }
.kpi .sub   { color: #94a3b8; font-size: .75rem; margin-top: 2px; }

.insight {
    background: white; border-left: 5px solid var(--accent);
    border-radius: 12px; padding: 12px 16px; margin-bottom: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05); font-size: .93rem; color: #334155;
}

.profile {
    background: linear-gradient(135deg, %%C1%%, %%C2%%);
    color: white; border-radius: 18px; padding: 22px 26px;
    box-shadow: 0 10px 24px rgba(0,0,0,0.18);
}
.profile h2 { margin: 0; font-size: 1.5rem; }
.badge {
    display: inline-block; padding: 4px 14px; border-radius: 999px;
    font-size: .8rem; font-weight: 600; color: white; margin-top: 8px;
}

div[data-testid="stVerticalBlockBorderWrapper"] { background: white; border-radius: 16px; }

button[data-baseweb="tab"] { font-weight: 600; font-size: .95rem; }

.stButton > button {
    width: 100%; color: white; border: none; border-radius: 12px; padding: .7rem 1rem;
    font-weight: 600; background: linear-gradient(135deg, %%C2%%, %%C3%%);
    box-shadow: 0 6px 16px rgba(0,0,0,0.20); transition: all .2s ease;
}
.stButton > button:hover { transform: translateY(-2px); color: white; filter: brightness(1.08); }

.stDownloadButton > button {
    width: 100%; color: white; border: none; border-radius: 12px; padding: .8rem 1rem;
    font-weight: 600; background: linear-gradient(135deg, %%C1%%, %%C2%%);
    box-shadow: 0 6px 16px rgba(0,0,0,0.15); transition: all .2s ease;
}
.stDownloadButton > button:hover { transform: translateY(-2px); color: white; filter: brightness(1.08); }

.app-footer {
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 999; text-align: center;
    padding: 12px 10px; color: white; font-size: .95rem; font-weight: 500; letter-spacing: .3px;
    background: linear-gradient(90deg, %%C1%%, %%C2%%, %%C3%%);
    box-shadow: 0 -4px 14px rgba(0,0,0,0.12);
}
</style>
"""
for key, val in {"%%C1%%": T["c1"], "%%C2%%": T["c2"], "%%C3%%": T["c3"],
                 "%%ACCENT%%": T["accent"], "%%BG1%%": T["bg1"], "%%BG2%%": T["bg2"]}.items():
    CSS = CSS.replace(key, val)
st.markdown(CSS, unsafe_allow_html=True)


# =========================================================
# HELPERS
# =========================================================
def kpi_card(icon, label, value, accent, sub=""):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    return f"""
    <div class="kpi" style="--accent:{accent};">
        <div class="icon">{icon}</div>
        <div class="value">{value}</div>
        <div class="label">{label}</div>{sub_html}
    </div>"""


def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def insight(text, accent=None):
    st.markdown(f'<div class="insight" style="--accent:{accent or T["accent"]};">{text}</div>',
                unsafe_allow_html=True)


def style_fig(fig, height=360):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Poppins, sans-serif", size=12, color="#334155"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    return fig


def get_mark_columns(df):
    """Columns created by the app: '<file name> / <max>'. Returns {column: max}."""
    cols = {}
    for c in df.columns:
        c = str(c)
        if " / " in c and pd.api.types.is_numeric_dtype(df[c]):
            try:
                cols[c] = float(c.rsplit(" / ", 1)[1])
            except ValueError:
                pass
    return cols


def to_excel_bytes(sheets: dict):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name[:31], index=False)
    return buf.getvalue()


PCT_COL = st.column_config.ProgressColumn("Percentage", format="%.1f%%", min_value=0, max_value=100)

# =========================================================
# HERO
# =========================================================
st.markdown(f"""
<div class="hero">
    <h1>📊 Student Performance Analysis Dashboard</h1>
    <p>Upload marksheet PDFs and get automatic insights, interactive charts and downloadable reports.</p>
    <span class="chip">📅 {datetime.now().strftime('%d %B %Y')}</span>
    <span class="chip">⚡ Instant analysis</span>
    <span class="chip">🔍 Student profiles</span>
    <span class="chip">📄 PDF &amp; Excel reports</span>
</div>
""", unsafe_allow_html=True)

# =========================================================
# RUN ANALYSIS
# =========================================================
if analyze_clicked:
    if not uploaded_files:
        st.sidebar.warning("Please upload at least one PDF marksheet.")
    else:
        try:
            with st.spinner("Analyzing marksheets..."):
                all_dfs = []
                for i, file in enumerate(uploaded_files):
                    df = extract_marks(file)
                    if "Marks" in df.columns:
                        df = df.rename(columns={"Marks": f"{file.name} / {max_marks[i]}"})
                    all_dfs.append(df)

                result = analyze(all_dfs, max_marks)
                generate_pdf(result, class_name, subject_name, teacher_name)

                try:
                    with open("report.pdf", "rb") as f:
                        pdf_bytes = f.read()
                except FileNotFoundError:
                    pdf_bytes = None

                st.session_state["result"] = result
                st.session_state["pdf_bytes"] = pdf_bytes
                st.session_state["meta"] = (class_name, subject_name, teacher_name)
                st.session_state["generated_at"] = datetime.now()
        except Exception as e:
            st.error(f"Something went wrong while analyzing the files: {e}")

# =========================================================
# DASHBOARD
# =========================================================
if "result" in st.session_state:
    result = st.session_state["result"].copy()
    r_class, r_subject, r_teacher = st.session_state["meta"]

    # Extra computed columns
    result["Rank"] = result["Percentage"].rank(ascending=False, method="min").astype(int)
    mark_cols = get_mark_columns(result)

    st.info(
        f"**Class:** {r_class}   |   **Subject:** {r_subject}   |   **Teacher:** {r_teacher}   |   "
        f"**Generated:** {st.session_state['generated_at'].strftime('%d %b %Y, %H:%M')}"
    )

    # ---- Core statistics
    avg = result["Percentage"].mean()
    median = result["Percentage"].median()
    highest = result["Percentage"].max()
    lowest = result["Percentage"].min()
    std = result["Percentage"].std() if len(result) > 1 else 0
    total = len(result)
    passed = int((result["Percentage"] >= pass_mark).sum())
    pass_rate = passed / total * 100 if total else 0
    excellent_n = int((result["Category"] == "Excellent").sum())
    weak_n = int((result["Category"] == "Weak").sum())

    tab_overview, tab_analytics, tab_students, tab_profile, tab_support, tab_reports = st.tabs(
        ["🏠 Overview", "📊 Analytics", "👥 Students", "🔍 Student Profile", "🆘 Support", "📥 Reports"]
    )

    # =====================================================
    # TAB 1 - OVERVIEW
    # =====================================================
    with tab_overview:
        section("📈 Class Overview")
        k = st.columns(6)
        k[0].markdown(kpi_card("🎓", "Class Average", f"{avg:.1f}%", T["accent"], f"Median {median:.1f}%"), unsafe_allow_html=True)
        k[1].markdown(kpi_card("👥", "Total Students", total, "#06b6d4"), unsafe_allow_html=True)
        k[2].markdown(kpi_card("✅", "Pass Rate", f"{pass_rate:.0f}%", "#22c55e", f"{passed} passed at {pass_mark}%"), unsafe_allow_html=True)
        k[3].markdown(kpi_card("🏆", "Excellent", excellent_n, "#10b981"), unsafe_allow_html=True)
        k[4].markdown(kpi_card("🆘", "Need Help", weak_n, "#ef4444"), unsafe_allow_html=True)
        k[5].markdown(kpi_card("📏", "Highest / Lowest", f"{highest:.0f} / {lowest:.0f}", "#8b5cf6", f"Std dev {std:.1f}"), unsafe_allow_html=True)

        st.write("")
        g1, g2, g3 = st.columns([1, 1, 1.2])

        with g1:
            with st.container(border=True):
                st.markdown("**Class Average**")
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=avg,
                    number={"suffix": "%", "font": {"size": 34}},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": T["accent"]},
                        "steps": [
                            {"range": [0, pass_mark], "color": "#fee2e2"},
                            {"range": [pass_mark, 75], "color": "#fef3c7"},
                            {"range": [75, 100], "color": "#d1fae5"},
                        ],
                        "threshold": {"line": {"color": "#111827", "width": 3}, "value": pass_mark},
                    },
                ))
                st.plotly_chart(style_fig(fig, 260), use_container_width=True)

        with g2:
            with st.container(border=True):
                st.markdown("**Pass vs Fail**")
                pf = pd.DataFrame({"Status": ["Passed", "Failed"], "Students": [passed, total - passed]})
                fig = px.pie(pf, names="Status", values="Students", hole=0.6,
                             color="Status", color_discrete_map={"Passed": "#22c55e", "Failed": "#ef4444"})
                fig.update_traces(textinfo="label+percent", marker=dict(line=dict(color="white", width=3)))
                fig.update_layout(showlegend=False)
                st.plotly_chart(style_fig(fig, 260), use_container_width=True)

        with g3:
            with st.container(border=True):
                st.markdown("**Category Distribution**")
                cat_counts = result["Category"].value_counts().reset_index()
                cat_counts.columns = ["Category", "Students"]
                cmap = {c: color_for(c, i) for i, c in enumerate(cat_counts["Category"])}
                fig = px.pie(cat_counts, names="Category", values="Students", hole=0.5,
                             color="Category", color_discrete_map=cmap)
                fig.update_traces(textinfo="label+percent", marker=dict(line=dict(color="white", width=3)))
                st.plotly_chart(style_fig(fig, 260), use_container_width=True)

        section("💡 Smart Insights")
        i1, i2 = st.columns(2)
        with i1:
            best = result.sort_values("Percentage", ascending=False).iloc[0]
            insight(f"🥇 <b>Top performer:</b> {best['Student Name']} with <b>{best['Percentage']:.1f}%</b>.", "#10b981")
            if avg >= 75:
                insight(f"🌟 The class is performing <b>very well</b> with an average of {avg:.1f}%.", "#10b981")
            elif avg >= pass_mark:
                insight(f"📘 The class average ({avg:.1f}%) is above the pass mark, with room to improve.", "#f59e0b")
            else:
                insight(f"🚨 The class average ({avg:.1f}%) is <b>below the pass mark</b> of {pass_mark}%.", "#ef4444")
        with i2:
            if std > 20:
                insight(f"📉 Results are <b>widely spread</b> (std dev {std:.1f}). Consider differentiated support.", "#f59e0b")
            else:
                insight(f"📊 Results are fairly consistent (std dev {std:.1f}).", "#3b82f6")
            if weak_n:
                insight(f"⚠️ <b>{weak_n}</b> student(s) are in the Weak category and need special attention.", "#ef4444")
            else:
                insight("🎉 No students are in the Weak category.", "#10b981")

    # =====================================================
    # TAB 2 - ANALYTICS
    # =====================================================
    with tab_analytics:
        section("📊 Score Distribution")
        a1, a2 = st.columns(2)

        with a1:
            with st.container(border=True):
                st.markdown("**Histogram of Percentages**")
                fig = px.histogram(result, x="Percentage", nbins=10, color_discrete_sequence=[T["accent"]])
                fig.update_traces(marker_line_color="white", marker_line_width=1.5)
                fig.add_vline(x=avg, line_dash="dash", line_color="#111827",
                              annotation_text=f"Avg {avg:.1f}%", annotation_position="top")
                fig.add_vline(x=pass_mark, line_dash="dot", line_color="#ef4444",
                              annotation_text=f"Pass {pass_mark}%", annotation_position="bottom")
                fig.update_layout(bargap=0.05, xaxis_title="Percentage", yaxis_title="Students")
                st.plotly_chart(style_fig(fig), use_container_width=True)

        with a2:
            with st.container(border=True):
                st.markdown("**Grade Bands**")
                bins = [0, 50, 60, 70, 80, 90, 100.01]
                labels = ["< 50", "50-59", "60-69", "70-79", "80-89", "90-100"]
                bands = pd.cut(result["Percentage"], bins=bins, labels=labels, right=False)
                band_df = bands.value_counts().reindex(labels).reset_index()
                band_df.columns = ["Band", "Students"]
                fig = px.bar(band_df, x="Band", y="Students", text="Students", color="Band",
                             color_discrete_sequence=["#ef4444", "#f97316", "#f59e0b", "#84cc16", "#22c55e", "#10b981"])
                fig.update_traces(textposition="outside")
                fig.update_layout(showlegend=False)
                st.plotly_chart(style_fig(fig), use_container_width=True)

        section("🏅 Top & Bottom Performers")
        b1, b2 = st.columns(2)
        with b1:
            with st.container(border=True):
                st.markdown("**Top 10 Students**")
                top = result.sort_values("Percentage", ascending=False).head(10).iloc[::-1]
                fig = px.bar(top, x="Percentage", y="Student Name", orientation="h", text="Percentage",
                             color="Percentage", color_continuous_scale=[T["c3"], T["c2"], T["c1"]])
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig.update_layout(coloraxis_showscale=False, xaxis_range=[0, 115], yaxis_title=None)
                st.plotly_chart(style_fig(fig, 400), use_container_width=True)
        with b2:
            with st.container(border=True):
                st.markdown("**Bottom 10 Students**")
                bottom = result.sort_values("Percentage").head(10).iloc[::-1]
                fig = px.bar(bottom, x="Percentage", y="Student Name", orientation="h", text="Percentage",
                             color="Percentage", color_continuous_scale=["#ef4444", "#f97316", "#f59e0b"])
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig.update_layout(coloraxis_showscale=False, xaxis_range=[0, 115], yaxis_title=None)
                st.plotly_chart(style_fig(fig, 400), use_container_width=True)

        if mark_cols:
            section("📚 Assessment Comparison")
            long = pd.DataFrame({
                "Assessment": [c.rsplit(" / ", 1)[0] for c, mx in mark_cols.items() for _ in range(len(result))],
                "Percentage": np.concatenate([(result[c] / mx * 100).to_numpy() for c, mx in mark_cols.items()]),
            })
            c1, c2 = st.columns(2)
            with c1:
                with st.container(border=True):
                    st.markdown("**Average per Assessment**")
                    avg_df = long.groupby("Assessment", as_index=False)["Percentage"].mean()
                    fig = px.bar(avg_df, x="Assessment", y="Percentage", text="Percentage",
                                 color="Assessment", color_discrete_sequence=px.colors.qualitative.Vivid)
                    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                    fig.update_layout(showlegend=False, yaxis_range=[0, 110], xaxis_title=None)
                    st.plotly_chart(style_fig(fig), use_container_width=True)
            with c2:
                with st.container(border=True):
                    st.markdown("**Spread per Assessment**")
                    fig = px.box(long, x="Assessment", y="Percentage", color="Assessment", points="all",
                                 color_discrete_sequence=px.colors.qualitative.Vivid)
                    fig.update_layout(showlegend=False, xaxis_title=None)
                    st.plotly_chart(style_fig(fig), use_container_width=True)

            if len(mark_cols) >= 2:
                with st.container(border=True):
                    st.markdown("**Correlation Between Assessments**")
                    corr_df = pd.DataFrame({c.rsplit(" / ", 1)[0]: result[c] for c in mark_cols}).corr()
                    fig = px.imshow(corr_df, text_auto=".2f", zmin=-1, zmax=1,
                                    color_continuous_scale="RdYlGn", aspect="auto")
                    st.plotly_chart(style_fig(fig, 360), use_container_width=True)

    # =====================================================
    # TAB 3 - STUDENTS (filterable table)
    # =====================================================
    with tab_students:
        section("📋 Student Results")
        f1, f2, f3 = st.columns([2, 2, 3])
        with f1:
            search = st.text_input("🔎 Search student", placeholder="Type a name...")
        with f2:
            cats = sorted(result["Category"].dropna().unique())
            chosen = st.multiselect("Category", cats, default=cats)
        with f3:
            lo, hi = st.slider("Percentage range", 0, 100, (0, 100))

        filtered = result[
            result["Category"].isin(chosen)
            & result["Percentage"].between(lo, hi)
            & result["Student Name"].astype(str).str.contains(search, case=False, na=False)
        ].sort_values("Percentage", ascending=False)

        st.caption(f"Showing **{len(filtered)}** of **{total}** students")
        ordered_cols = ["Rank"] + [c for c in filtered.columns if c != "Rank"]
        with st.container(border=True):
            st.dataframe(
                filtered[ordered_cols], use_container_width=True, hide_index=True,
                column_config={"Percentage": PCT_COL},
            )
        st.download_button(
            "⬇ Download filtered list (CSV)",
            filtered[ordered_cols].to_csv(index=False).encode("utf-8"),
            "filtered_students.csv", "text/csv",
        )

    # =====================================================
    # TAB 4 - STUDENT PROFILE
    # =====================================================
    with tab_profile:
        section("🔍 Individual Student Profile")
        names = result.sort_values("Student Name")["Student Name"].tolist()
        selected = st.selectbox("Select a student", names)
        s = result[result["Student Name"] == selected].iloc[0]
        percentile = (result["Percentage"] < s["Percentage"]).mean() * 100
        diff = s["Percentage"] - avg
        badge_color = color_for(s["Category"])

        p1, p2 = st.columns([1.2, 2])
        with p1:
            st.markdown(f"""
            <div class="profile">
                <div style="font-size:2.4rem;">🎓</div>
                <h2>{s['Student Name']}</h2>
                <span class="badge" style="background:{badge_color};">{s['Category']}</span>
                <div style="margin-top:16px;font-size:2.2rem;font-weight:700;">{s['Percentage']:.1f}%</div>
                <div style="opacity:.9;">Rank <b>{int(s['Rank'])}</b> of {total} &nbsp;|&nbsp; Top <b>{100 - percentile:.0f}%</b></div>
                <div style="opacity:.9;margin-top:6px;">{'▲' if diff >= 0 else '▼'} {abs(diff):.1f} pts {'above' if diff >= 0 else 'below'} class average</div>
            </div>
            """, unsafe_allow_html=True)

        with p2:
            with st.container(border=True):
                if mark_cols:
                    rows = []
                    for c, mx in mark_cols.items():
                        label = c.rsplit(" / ", 1)[0]
                        rows.append({"Assessment": label, "Who": selected, "Percentage": s[c] / mx * 100})
                        rows.append({"Assessment": label, "Who": "Class average", "Percentage": result[c].mean() / mx * 100})
                    comp = pd.DataFrame(rows)
                    fig = px.bar(comp, x="Assessment", y="Percentage", color="Who", barmode="group",
                                 text="Percentage",
                                 color_discrete_map={selected: T["accent"], "Class average": "#cbd5e1"})
                    fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
                    fig.update_layout(yaxis_range=[0, 115], xaxis_title=None)
                    st.markdown("**Student vs Class Average**")
                    st.plotly_chart(style_fig(fig, 320), use_container_width=True)
                else:
                    fig = go.Figure(go.Bar(
                        x=["Student", "Class average", "Highest"],
                        y=[s["Percentage"], avg, highest],
                        marker_color=[T["accent"], "#cbd5e1", "#10b981"],
                        text=[f"{v:.1f}%" for v in (s["Percentage"], avg, highest)], textposition="outside",
                    ))
                    fig.update_layout(yaxis_range=[0, 115])
                    st.markdown("**Student vs Class**")
                    st.plotly_chart(style_fig(fig, 320), use_container_width=True)

        if s["Percentage"] < pass_mark:
            st.error(f"{selected} is **below the pass mark** by {pass_mark - s['Percentage']:.1f} points.")
        elif s["Category"] == "Weak":
            st.warning(f"{selected} is in the Weak category. Consider extra support.")
        else:
            st.success(f"{selected} is performing well.")

    # =====================================================
    # TAB 5 - SUPPORT
    # =====================================================
    with tab_support:
        section("⚠️ Students Needing Special Help")
        weak_df = result[result["Category"] == "Weak"]
        if len(weak_df) > 0:
            st.warning(f"{len(weak_df)} student(s) are in the Weak category.")
            with st.container(border=True):
                st.dataframe(
                    weak_df.sort_values("Percentage")[["Rank", "Student Name", "Percentage"]],
                    use_container_width=True, hide_index=True,
                    column_config={"Percentage": PCT_COL},
                )
        else:
            st.success("No students currently in weak category 🎉")

        section("🎯 At-Risk Watchlist")
        st.caption(f"Students below the pass mark ({pass_mark}%) or within 10 points above it.")
        risk = result[result["Percentage"] < pass_mark + 10].copy()
        risk["Gap to pass mark"] = (risk["Percentage"] - pass_mark).round(1)
        risk["Status"] = np.where(risk["Percentage"] < pass_mark, "🔴 Failing", "🟠 Borderline")
        if len(risk):
            with st.container(border=True):
                st.dataframe(
                    risk.sort_values("Percentage")[["Rank", "Student Name", "Percentage", "Gap to pass mark", "Status"]],
                    use_container_width=True, hide_index=True,
                    column_config={"Percentage": PCT_COL},
                )
        else:
            st.success("Nobody is at risk 🎉")

    # =====================================================
    # TAB 6 - REPORTS
    # =====================================================
    with tab_reports:
        section("📥 Download Reports")

        summary_df = pd.DataFrame({
            "Metric": ["Class", "Subject", "Teacher", "Total students", "Class average (%)", "Median (%)",
                       "Highest (%)", "Lowest (%)", "Std deviation", f"Pass rate at {pass_mark}% (%)",
                       "Excellent students", "Weak students"],
            "Value": [r_class, r_subject, r_teacher, total, round(avg, 2), round(median, 2),
                      round(highest, 2), round(lowest, 2), round(std, 2), round(pass_rate, 2),
                      excellent_n, weak_n],
        })
        excel_bytes = to_excel_bytes({
            "Results": result.sort_values("Percentage", ascending=False),
            "Summary": summary_df,
            "Weak Students": weak_df if len(weak_df) else pd.DataFrame({"Info": ["No weak students"]}),
        })

        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button("⬇ Excel Report (3 sheets)", excel_bytes, "student_analysis.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with d2:
            st.download_button("⬇ Results (CSV)", result.to_csv(index=False).encode("utf-8"),
                               "student_results.csv", "text/csv")
        with d3:
            if st.session_state.get("pdf_bytes"):
                st.download_button("⬇ PDF Report", st.session_state["pdf_bytes"],
                                   "student_report.pdf", "application/pdf")
            else:
                st.info("PDF report not available.")

        section("🧾 Summary")
        with st.container(border=True):
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

else:
    # ---- Welcome / empty state
    section("👋 Getting Started")
    w1, w2, w3 = st.columns(3)
    w1.markdown(kpi_card("1️⃣", "Upload your PDF marksheets in the sidebar", "Upload", T["accent"]), unsafe_allow_html=True)
    w2.markdown(kpi_card("2️⃣", "Choose class, teacher, subject, pass mark and max marks", "Configure", "#06b6d4"), unsafe_allow_html=True)
    w3.markdown(kpi_card("3️⃣", "Click “Analyze Students” to unlock the dashboard", "Analyze", "#10b981"), unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown('<div class="app-footer">Developed by Danny NIYITANGA</div>', unsafe_allow_html=True)