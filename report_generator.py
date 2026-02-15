from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from datetime import datetime


def generate_pdf(df, class_name, subject_name, teacher_name, filename="report.pdf"):

    # -------------------------
    # DOCUMENT SETUP (LANDSCAPE)
    # -------------------------
    doc = SimpleDocTemplate(
        filename,
        pagesize=landscape(A4),
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    elements = []
    styles = getSampleStyleSheet()

    # -------------------------
    # CUSTOM STYLES
    # -------------------------
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.darkblue,
        alignment=1,
        spaceAfter=10
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        textColor=colors.darkblue,
        spaceAfter=8
    )

    normal_style = styles["Normal"]

    # -------------------------
    # TITLE & META INFORMATION
    # -------------------------
    elements.append(Paragraph("📊 STUDENT PERFORMANCE REPORT", title_style))
    elements.append(Spacer(1, 5))

    meta_data = [
        f"<b>Class:</b> {class_name}",
        f"<b>Subject:</b> {subject_name}",
        f"<b>Teacher:</b> {teacher_name}",
        f"<b>Generated Date:</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
    ]

    for line in meta_data:
        elements.append(Paragraph(line, normal_style))

    elements.append(Spacer(1, 12))

    # -------------------------
    # SUMMARY TABLE
    # -------------------------
    avg = df["Percentage"].mean()
    total_students = len(df)
    counts = df["Category"].value_counts()

    summary_data = [
        ["Metric", "Value"],
        ["Class Average", f"{avg:.2f}%"],
        ["Total Students", total_students],
        ["Excellent", counts.get("Excellent", 0)],
        ["Good", counts.get("Good", 0)],
        ["Fair", counts.get("Fair", 0)],
        ["Weak", counts.get("Weak", 0)],
    ]

    summary_table = Table(summary_data, colWidths=[250, 250])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # -------------------------
    # CHARTS: PIE + BAR
    # -------------------------
    elements.append(Paragraph("📊 Performance Overview", heading_style))

    draw = Drawing(800, 250)

    categories_order = ["Excellent", "Good", "Fair", "Weak"]
    pie_data = [counts.get(cat, 0) for cat in categories_order]

    pie = Pie()
    pie.x = 0
    pie.y = 50
    pie.width = 150
    pie.height = 150
    pie.data = pie_data
    pie.labels = categories_order
    pie.slices[0].fillColor = colors.lightgreen
    pie.slices[1].fillColor = colors.lightblue
    pie.slices[2].fillColor = colors.lightyellow
    pie.slices[3].fillColor = colors.salmon
    draw.add(pie)

    # BAR CHART (Top 5 students)
    top_students = df.sort_values("Percentage", ascending=False).head(5)

    bc = VerticalBarChart()
    bc.x = 250
    bc.y = 40
    bc.height = 200
    bc.width = 400
    bc.data = [list(top_students["Percentage"])]
    bc.categoryAxis.categoryNames = list(top_students["Student Name"])
    bc.barWidth = 10
    bc.bars[0].fillColor = colors.blue
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = 100
    bc.valueAxis.valueStep = 10
    bc.categoryAxis.labels.boxAnchor = "e"
    bc.categoryAxis.labels.angle = 90

    draw.add(bc)

    elements.append(draw)
    elements.append(Spacer(1, 20))

    # -------------------------
    # FINAL RESULTS TABLE
    # -------------------------
    elements.append(Paragraph("📋 Final Result Table", heading_style))

    sorted_df = df.sort_values("Percentage", ascending=False)
    sorted_df["Percentage"] = sorted_df["Percentage"].map(lambda x: f"{x:.2f}")

    columns = list(sorted_df.columns)
    table_data = [columns] + [
        [row[col] for col in columns] for _, row in sorted_df.iterrows()
    ]

    col_widths = [
        160 if "Name" in c else 100 if "Category" in c else 70
        for c in columns
    ]

    results_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
    ])

    category_col_index = columns.index("Category")

    for i in range(1, len(table_data)):
        cat = table_data[i][category_col_index]
        color = (
            colors.lightgreen if cat == "Excellent"
            else colors.lightblue if cat == "Good"
            else colors.lightyellow if cat == "Fair"
            else colors.salmon
        )
        style.add("BACKGROUND", (category_col_index, i), (category_col_index, i), color)

    results_table.setStyle(style)
    elements.append(results_table)
    elements.append(Spacer(1, 20))

    # -------------------------
    # STUDENTS NEEDING HELP
    # -------------------------
    elements.append(Paragraph("⚠ Students Needing Special Help", heading_style))

    weak_students = df[df["Category"] == "Weak"]

    if len(weak_students) == 0:
        elements.append(Paragraph("No students need special help.", normal_style))
    else:
        weak_data = [["Student Name", "Percentage", "Status"]] + [
            [
                row["Student Name"],
                f"{row['Percentage']:.2f}%",   # ✅ Two decimal places
                "Needs Support"
            ]
            for _, row in weak_students.iterrows()
        ]

        weak_table = Table(weak_data, colWidths=[200, 100, 150])

        weak_table_style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkred),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])

        for i in range(1, len(weak_data)):
            weak_table_style.add("BACKGROUND", (0, i), (-1, i), colors.salmon)

        weak_table.setStyle(weak_table_style)
        elements.append(weak_table)
        elements.append(Spacer(1, 20))

    # -------------------------
    # BUILD PDF
    # -------------------------
    doc.build(elements)
    print(f"PDF generated successfully: {filename}")
