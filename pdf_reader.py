import pdfplumber
import re
import pandas as pd

def extract_marks(pdf_file):
    data = []

    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue

            for line_num, line in enumerate(text.split("\n"), start=1):
                line = line.strip()

                # 🚫 Skip unwanted lines
                if "Academic Year" in line:
                    continue

                # Regex for reg number, name and marks
                match = re.match(r'(\d[\d\-]*)?\s*([^\d\n]+?)\s+([\d\.]+)$', line)

                if match:
                    reg = match.group(1) if match.group(1) else "N/A"
                    name = match.group(2).strip()
                    mark = float(match.group(3))

                    if mark == 0.01:
                        mark = 0

                    data.append([reg, name, mark])

    df = pd.DataFrame(data, columns=["Reg Number", "Student Name", "Marks"])
    return df
