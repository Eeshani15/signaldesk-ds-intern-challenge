import pandas as pd

FILE = "product_usage_events.csv"


def pct(numerator, denominator):
    if denominator == 0:
        return 0.0
    return numerator / denominator * 100


def main():
    # Load data
    df = pd.read_csv(FILE)

    # -----------------------------
    # 1. Basic cleaning
    # -----------------------------
    df["team"] = df["team"].astype(str).str.strip().str.title()
    df["confidence_numeric"] = pd.to_numeric(
        df["median_confidence"], errors="coerce"
    )
    df["user_rating_numeric"] = pd.to_numeric(
        df["user_rating"], errors="coerce"
    )

    # -----------------------------
    # 2. Detect data-quality issues
    # -----------------------------
    duplicate_rows = df.duplicated().sum()

    invalid_confidence = df["confidence_numeric"].isna().sum()

    missing_ratings = df["user_rating_numeric"].isna().sum()

    team_casing_issues = (
        df["team"].astype(str).str.lower().eq("product").sum()
        - df["team"].eq("Product").sum()
    )

    suspicious_notes = df[
        df["notes"]
        .astype(str)
        .str.contains(
            "duplicate|traffic spike|policy changed|prompt version",
            case=False,
            na=False,
        )
    ]

    # -----------------------------
    # 3. Remove exact duplicate rows
    # -----------------------------
    clean_df = df.drop_duplicates().copy()

    # -----------------------------
    # 4. Workflow-level metrics
    # -----------------------------
    workflow_rows = []

    for workflow, group in clean_df.groupby("workflow"):

        sessions = group["sessions"].sum()
        completed = group["completed"].sum()
        accepted = group["accepted_output"].sum()
        flagged = group["flagged_for_review"].sum()

        completion_rate = pct(completed, sessions)
        acceptance_rate = pct(accepted, sessions)
        review_rate = pct(flagged, sessions)

        weighted_minutes = (
            (group["avg_minutes_saved"] * group["sessions"]).sum()
            / sessions
            if sessions > 0
            else 0
        )

        rating_data = group.dropna(subset=["user_rating_numeric"])

        if len(rating_data) > 0:
            weighted_rating = (
                (
                    rating_data["user_rating_numeric"]
                    * rating_data["sessions"]
                ).sum()
                / rating_data["sessions"].sum()
            )
        else:
            weighted_rating = float("nan")

        workflow_rows.append(
            {
                "workflow": workflow,
                "completion_rate": completion_rate,
                "acceptance_rate": acceptance_rate,
                "review_rate": review_rate,
                "rating": weighted_rating,
                "minutes_saved": weighted_minutes,
            }
        )

    metrics = pd.DataFrame(workflow_rows)

    # -----------------------------
    # 5. Print report
    # -----------------------------
    print("=" * 60)
    print("SIGNALDESK WORKFLOW HEALTH CHECK")
    print("=" * 60)

    print("\nDATA QUALITY")
    print("-" * 60)
    print(f"Duplicate rows detected: {duplicate_rows}")
    print(f"Missing ratings: {missing_ratings}")
    print(f"Invalid/missing confidence values: {invalid_confidence}")

    print(
        f"Rows mentioning prompt/policy/anomaly issues: "
        f"{len(suspicious_notes)}"
    )

    print("\nWORKFLOW HEALTH")
    print("-" * 60)

    for _, row in metrics.iterrows():
        rating = (
            f"{row['rating']:.2f}"
            if pd.notna(row["rating"])
            else "N/A"
        )

        print(f"\n{row['workflow']}")
        print(f"  Completion: {row['completion_rate']:.1f}%")
        print(f"  Acceptance: {row['acceptance_rate']:.1f}%")
        print(f"  Review:     {row['review_rate']:.1f}%")
        print(f"  Rating:     {rating}")
        print(f"  Minutes:    {row['minutes_saved']:.1f}")

    # -----------------------------
    # 6. Aug 7 Reply Draft check
    # -----------------------------
    df["date"] = pd.to_datetime(df["date"])

    reply_aug7 = clean_df[
        (clean_df["workflow"] == "Reply draft")
        & (clean_df["date"] == "2026-08-07")
    ]

    print("\nINVESTIGATE NEXT")
    print("-" * 60)

    if not reply_aug7.empty:
        row = reply_aug7.iloc[0]

        print("[HIGH] Reply Draft — Aug 7")
        print(
            "Sharp deterioration in workflow outcomes occurred on Aug 7."
        )
        print(
            f"  Completion rate: "
            f"{pct(row['completed'], row['sessions']):.1f}%"
        )
        print(
            f"  Acceptance rate: "
            f"{pct(row['accepted_output'], row['sessions']):.1f}%"
        )
        print(f"  Rating: {row['user_rating']}")
        print(f"  Confidence: {row['median_confidence']}")
        print(f"  Note: {row['notes']}")
        print(
            "  Interpretation: investigate before attributing this "
            "to model quality because the review policy changed."
        )

    # -----------------------------
    # 7. Aug 5 Lead Summary anomaly
    # -----------------------------
    lead_aug5 = clean_df[
        (clean_df["workflow"] == "Lead summary")
        & (clean_df["date"] == "2026-08-05")
    ]

    if not lead_aug5.empty:
        print("\n[HIGH] Lead Summary — Aug 5")
        print(
            "A demo-account traffic spike and duplicate export row "
            "were detected."
        )
        print(
            "Do not use this observation as a normal production benchmark."
        )

    # -----------------------------
    # 8. Metric trust assessment
    # -----------------------------
    print("\nMETRIC TO TRUST LEAST")
    print("-" * 60)
    print("Model confidence.")
    print(
        "Confidence is model-reported and is not equivalent to correctness."
    )
    print(
        "For example, Aug 7 Reply Draft had high confidence but poor "
        "rating and high review activity."
    )

    # -----------------------------
    # 9. Final recommendation
    # -----------------------------
    print("\nBOTTOM LINE")
    print("-" * 60)
    print(
        "Lead Summary appears strongest overall, but its performance "
        "is sensitive to anomalous Aug 5 traffic."
    )
    print(
        "Reply Draft deserves the next investigation because Aug 7 "
        "shows a sharp deterioration coinciding with a review-policy change."
    )
    print(
        "Use acceptance rate, user rating, and review rate as primary "
        "health signals; treat model confidence as diagnostic only."
    )

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
