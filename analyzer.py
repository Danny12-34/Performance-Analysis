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

    # Exclude non-score metadata columns so dynamic headers like 'filename.pdf / max' work smoothly
    non_score_cols = ["Reg Number", "Student Name", "Total Earned", "Percentage", "Category"]
    mark_cols = [c for c in merged.columns if c not in non_score_cols]

    # 1. Sum total earned marks across all tests for each student
    merged["Total Earned"] = merged[mark_cols].sum(axis=1)

    # 2. Sum the total possible marks from your sidebar input list
    total_possible_marks = sum(max_marks)

    # 3. Calculate final percentage: (Total Earned / Total Possible) * 100
    if total_possible_marks > 0:
        merged["Percentage"] = (merged["Total Earned"] / total_possible_marks) * 100
    else:
        merged["Percentage"] = 0.0

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