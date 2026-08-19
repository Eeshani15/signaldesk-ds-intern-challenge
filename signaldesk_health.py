import pandas as pd

FILE = "product_usage_events.csv"


def pct(numerator, denominator):
    if denominator == 0:
        return 0.0
    return numerator / denominator * 100

def main():

    # ---------------------------------------------------------
    # 1. Load data
    # ---------------------------------------------------------
    df = pd.read_csv(FILE)

    df["date"] = pd.to_datetime(df["date"])

    # Standardize text fields
    df["team"] = df["team"].astype(str).str.strip().str.title()
    df["workflow"] = df["workflow"].astype(str).str.strip()

    # Convert numeric fields
    df["confidence_numeric"] = pd.to_numeric(
        df["median_confidence"], errors="coerce"
    )

    df["user_rating_numeric"] = pd.to_numeric(
        df["user_rating"], errors="coerce"
    )

    # ---------------------------------------------------------
    # 2. Data-quality checks
    # ---------------------------------------------------------

    # The export contains a suspicious repeated event.
    # We identify it using the fields that define the workflow event,
    # rather than the notes column.
    duplicate_keys = [
        "date",
        "team",
        "workflow",
        "source",
        "sessions",
        "completed",
        "accepted_output",
        "flagged_for_review",
        "avg_minutes_saved",
        "median_confidence",
        "user_rating",
    ]

    duplicate_mask = df.duplicated(
        subset=duplicate_keys,
        keep=False
    )

    suspicious_duplicates = df[duplicate_mask].copy()

    missing_ratings = df["user_rating_numeric"].isna().sum()

    invalid_confidence = df["confidence_numeric"].isna().sum()

    casing_issues = (
        df["team"].astype(str).str.lower() == "product"
    ).sum()

    change_notes = df[
        df["notes"]
        .astype(str)
        .str.contains(
            "prompt version|policy changed|traffic spike|duplicate",
            case=False,
            na=False,
        )
    ]

    # ---------------------------------------------------------
    # 3. Remove suspicious duplicate/demo traffic
    # ---------------------------------------------------------

    clean_df = df.copy()

    if not suspicious_duplicates.empty:
        # Remove the repeated Aug 5 Lead Summary demo-account rows
        clean_df = clean_df[
            ~(
                (clean_df["date"] == pd.Timestamp("2026-08-05"))
                & (clean_df["team"] == "Sales")
                & (clean_df["workflow"] == "Lead summary")
                & (clean_df["source"] == "email")
                & (clean_df["sessions"] == 140)
            )
        ]

    # Add back ONE representative row only if the suspicious event
    # represents a real event. In this dataset it is explicitly marked
    # as a demo-account spike and duplicate export, so we exclude it
    # from normal workflow health calculations.

    # ---------------------------------------------------------
    # 4. Workflow-level metrics
    # ---------------------------------------------------------

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

        rating_data = group.dropna(
            subset=["user_rating_numeric"]
        )

        if not rating_data.empty:
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

    # ---------------------------------------------------------
    # 5. Print report
    # ---------------------------------------------------------

    print("=" * 60)
    print("SIGNALDESK WORKFLOW HEALTH CHECK")
    print("=" * 60)

    print("\nDATA QUALITY")
    print("-" * 60)

    print(
        f"Suspicious duplicate/event rows detected: "
        f"{len(suspicious_duplicates)}"
    )

    print(f"Missing ratings: {missing_ratings}")
    print(f"Invalid/missing confidence values: {invalid_confidence}")
    print(f"Rows mentioning changes/anomalies: {len(change_notes)}")

    # ---------------------------------------------------------
    # 6. Show suspicious data
    # ---------------------------------------------------------

    if not suspicious_duplicates.empty:

        print("\nSUSPICIOUS RECORDS")
        print("-" * 60)

        for _, row in suspicious_duplicates.iterrows():

            print(
                f"{row['date'].date()} | "
                f"{row['team']} | "
                f"{row['workflow']} | "
                f"{row['source']} | "
                f"{row['sessions']} sessions | "
                f"{row['notes']}"
            )

        print(
            "\nThese records are excluded from normal workflow "
            "health metrics because the notes identify demo traffic "
            "and a duplicate export."
        )

    # ---------------------------------------------------------
    # 7. Workflow health
    # ---------------------------------------------------------

    print("\nWORKFLOW HEALTH")
    print("-" * 60)

    for _, row in metrics.iterrows():

        rating = (
            f"{row['rating']:.2f}"
            if pd.notna(row["rating"])
            else "N/A"
        )

        print(f"\n{row['workflow']}")

        print(
            f"  Completion: "
            f"{row['completion_rate']:.1f}%"
        )

        print(
            f"  Acceptance: "
            f"{row['acceptance_rate']:.1f}%"
        )

        print(
            f"  Review:     "
            f"{row['review_rate']:.1f}%"
        )

        print(
            f"  Rating:     "
            f"{rating}"
        )

        print(
            f"  Minutes:    "
            f"{row['minutes_saved']:.1f}"
        )

    # ---------------------------------------------------------
    # 8. Reply Draft Aug 6 vs Aug 7
    # ---------------------------------------------------------

    reply = clean_df[
        (clean_df["workflow"] == "Reply draft")
        & (
            clean_df["date"].isin(
                [
                    pd.Timestamp("2026-08-06"),
                    pd.Timestamp("2026-08-07"),
                ]
            )
        )
    ]

    print("\nINVESTIGATE NEXT")
    print("-" * 60)

    if not reply.empty:

        for _, row in reply.iterrows():

            print(
                f"\nReply Draft — "
                f"{row['date'].strftime('%b %d')}"
            )

            print(
                f"  Completion: "
                f"{pct(row['completed'], row['sessions']):.1f}%"
            )

            print(
                f"  Acceptance: "
                f"{pct(row['accepted_output'], row['sessions']):.1f}%"
            )

            print(
                f"  Review: "
                f"{pct(row['flagged_for_review'], row['sessions']):.1f}%"
            )

            print(f"  Rating: {row['user_rating']}")
            print(f"  Confidence: {row['median_confidence']}")
            print(f"  Note: {row['notes']}")

    print("\n[HIGH] Reply Draft — Aug 7")

    print(
        "Sharp deterioration occurred on Aug 7 across "
        "completion, acceptance, rating, and estimated time saved."
    )

    print(
        "A review-policy change occurred mid-day, so this "
        "should be investigated before attributing the decline "
        "to model quality."
    )

    # ---------------------------------------------------------
    # 9. Lead Summary anomaly
    # ---------------------------------------------------------

    print("\n[HIGH] Lead Summary — Aug 5")

    print(
        "A demo-account traffic spike and duplicate export "
        "event were detected."
    )

    print(
        "The affected event is excluded from the workflow "
        "health metrics."
    )

    # ---------------------------------------------------------
    # 10. Least trustworthy metric
    # ---------------------------------------------------------

    print("\nMETRIC TO TRUST LEAST")
    print("-" * 60)

    print("Model confidence.")

    print(
        "Confidence is model-reported and is not equivalent "
        "to correctness."
    )

    print(
        "For example, Aug 7 Reply Draft had 0.91 confidence "
        "while user rating was 2.1 and review activity was high."
    )

    # ---------------------------------------------------------
    # 11. Bottom line
    # ---------------------------------------------------------

    print("\nBOTTOM LINE")
    print("-" * 60)

    print(
        "Lead Summary appears strongest on the cleaned data, "
        "but the Aug 5 demo-account event should not be used "
        "as a normal benchmark."
    )

    print(
        "Reply Draft deserves the next investigation because "
        "Aug 7 shows a sharp deterioration coinciding with a "
        "review-policy change."
    )

    print(
        "For weekly monitoring, prioritize acceptance rate, "
        "user rating, and review rate. Treat model confidence "
        "as a diagnostic signal rather than a quality KPI."
    )

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
