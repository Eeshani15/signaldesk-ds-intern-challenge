# SignalDesk Workflow Health Check

## Track

Track A — Fictional Domain Packet

## What I Built

A lightweight Python health check that helps the SignalDesk team identify which AI-assisted workflows look healthy, which records may be misleading, and what deserves investigation next.

The script calculates workflow-level completion, acceptance, review, user-rating, and estimated time-saved metrics while checking for suspicious records and data-quality issues.

## Who It's For

SignalDesk product or operations teammates deciding what to investigate before expanding AI-assisted workflows.

## Data

I used the provided fictional `product_usage_events.csv` dataset.

## Assumptions

* Sessions represent workflow runs, not unique users.
* Acceptance is treated as a rough quality signal.
* Model confidence is not treated as correctness.
* Estimated minutes saved is directional.
* Workflow rates are calculated from aggregated counts rather than averaging daily percentages.

## Issues Noticed

The data contains a duplicate/demo-account event on Aug 5, missing ratings, non-numeric confidence, inconsistent team casing, and a review-policy change on Aug 7.

The Aug 7 Reply Draft row shows a sharp decline in completion, acceptance, rating, and estimated time saved. Because the review policy changed mid-day, I did not attribute the decline directly to model quality.

## What I Would Do Next

I would establish a stable evaluation set, standardize review-policy definitions, collect more observations, and compare workflow outcomes before and after changes under consistent conditions.
