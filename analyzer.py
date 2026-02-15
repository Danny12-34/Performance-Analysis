import pandas as pd

def analyze(all_dfs, max_marks):

    merged = all_dfs[0]

    for i, df in enumerate(all_dfs[1:], start=1):
        merged = merged.merge(
            df,
            on=["Reg Number", "Student Name"],
            how="outer",
            suffixes=(None, f"_{i}")
        )

    merged = merged.fillna(0)

    mark_cols = [c for c in merged.columns if "Marks" in c]

    total_percent = 0

    for i, col in enumerate(mark_cols):
        total_percent += merged[col] / max_marks[i]

    merged["Percentage"] = (total_percent / len(mark_cols)) * 100

    def grade(p):
        if p >= 80:
            return "Excellent"
        elif p >= 65:
            return "Good"
        elif p >= 50:
            return "Fair"
        else:
            return "Weak"

    merged["Category"] = merged["Percentage"].apply(grade)

    return merged
    