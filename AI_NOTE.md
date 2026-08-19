# AI Note

## Did I use AI?

Yes.

## How I used it

I used AI to help interpret the domain packet, brainstorm a small teammate-facing artifact, review data-cleaning and metric calculations, and challenge possible interpretations of the messy observations.

One useful workflow was providing the domain description and dataset and asking AI to identify potential data-quality problems and suggest a small artifact that would help a teammate decide what to investigate next.

## What AI helped with

AI helped identify several important analysis directions, including the Aug 5 Lead Summary anomaly, the Aug 7 Reply Draft deterioration, and the distinction between model confidence and actual output quality.

## What I verified myself

I independently checked the underlying rows and metric calculations before using them in the final recommendation. I also verified that the Aug 5 event was explicitly associated with demo traffic and a duplicate export issue.

I chose not to treat model confidence as a quality metric and did not claim that the Aug 7 Reply Draft decline was caused by the model. The dataset says the review policy changed mid-day, so the observed deterioration could partly reflect that policy change.

The final scope and recommendation were my own decisions: keep the artifact small, prioritize investigation over prediction, and focus weekly monitoring on acceptance rate, user rating, and review rate.
