# One-Page Reflection: When Bayes Changed the Decision

**Name:** Roja Shrestha
**Assignment:** W6 — Probabilistic Models
**Date:** June 2026

---

## The Concrete Example

In Part 6 (Bayesian Logistic Regression on Telco Churn), the MLE gave a single-point estimate for the coefficient of `tenure` — something like β ≈ −0.043 — which would lead you to conclude: *"Longer tenure decreases churn probability, so we should focus retention efforts on new customers."* That sounds clean and actionable.

But when the fully Bayesian model was run using PyMC, the posterior for that same `tenure` coefficient was wide and overlapped zero substantially — roughly 94% HDI spanning [−0.091, +0.004]. The MLE showed a peak and called it a day; the Bayesian model showed the entire distribution, which told a very different story.

---

## The Decision That Changed

**MLE decision:** Deploy a targeted churn-intervention campaign specifically for low-tenure customers, treating tenure as a reliable predictor.

**Bayesian decision:** Do *not* rely on tenure alone. The posterior uncertainty is too large — there is meaningful probability mass on β > 0, meaning tenure might not even have a negative effect on churn for this segment. Instead, prioritise features with tight, confidently-signed posteriors (e.g., `Contract_Month-to-month`) where the posterior was concentrated far from zero.

---

## The Mechanism

The MLE maximises the likelihood and returns the single best-fitting parameter value, with no representation of how *confident* that estimate is given the data. It treats the peak as the whole answer.

The Bayesian posterior, in contrast, integrates over all plausible parameter values weighted by both likelihood and prior. When data is limited or the signal is weak, the posterior stays wide — and that width is itself the answer. A wide posterior on `tenure` says: *"The data doesn't strongly support this coefficient; don't over-commit to it."*

In practice, the mechanism is: **MLE ignores parameter uncertainty → overstates decision confidence → leads to over-specification of strategy**. The Bayesian HDI makes uncertainty explicit, forcing a more cautious, evidence-proportionate decision. The model didn't just give a number — it showed the full distribution it never hides.

---

*"A model that gives you a number is giving you the peak of a distribution it never shows you. Probabilistic models make the full distribution explicit."*
