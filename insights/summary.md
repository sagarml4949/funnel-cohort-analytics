# Insights & Recommendations — E-commerce Funnel & Cohort Analysis

*This is written the way a PM would present findings to a cross-functional
review — problem, evidence, hypothesis, recommendation, guardrail metric.*

## Finding 1: Footwear has the weakest mid-funnel conversion

**Evidence:** Footwear converts view→cart at a normal rate (30.8%, in line
with other categories) but drops sharply at cart→checkout (46.3% — the
lowest of all 6 categories, vs. 55.6% for Ethnic Wear). It also carries the
highest return rate in the catalog.

**Hypothesis:** Users add shoes to cart while browsing size options, but
abandon at checkout because they're unsure which size to commit to — the
same uncertainty that later drives returns. This is a **fit-confidence
problem**, not a demand or pricing problem (view volume and view→cart are
both healthy).

**Recommendation:** Ship a checkout-stage size-confidence intervention
(e.g., a size-recommendation prompt using purchase-return history, or a
prominent "free size exchange" badge) as an A/B test on the Footwear
category before broader rollout.

**Guardrail metric:** Return rate should not increase even if checkout
conversion rises — an increase would mean the intervention encouraged
provisional purchases rather than solving fit uncertainty. *(This exact
problem — and a working prototype size-recommendation model — is the
subject of the companion "Size-Fit Product Sense" project.)*

## Finding 2: Paid Social and Influencer are the least efficient acquisition channels

**Evidence:** Paid Social costs ₹4,294 CAC and returns only ₹692 revenue/user
in the observed window (ROI multiple 0.16x). Influencer is similarly weak
(₹3,777 CAC, 0.18x ROI). Organic Search, by contrast, returns 0.80x at a
CAC of ₹805 — 5x more capital-efficient.

**Hypothesis:** Paid Social and Influencer are likely doing their job for
top-of-funnel awareness/reach, but the ROI framing here (revenue captured
within the modeled window) suggests they're overweighted relative to
higher-intent channels like Organic Search and Referral.

**Recommendation:** Reallocate 10-15% of Paid Social budget toward Organic
Search (SEO/content) and Referral program incentives, and monitor whether
overall new-user volume holds steady while blended CAC falls.

**Guardrail metric:** Total new-user acquisition volume — efficiency gains
that come at the cost of top-of-funnel volume are a false win.

## Finding 3: Retention needs to be read alongside AOV, not instead of it

**Evidence:** Monthly KPIs show AOV and revenue both fluctuate month to
month, but a rising AOV can mask a shrinking, less-loyal user base if
repeat purchase rate isn't tracked alongside it.

**Recommendation:** Before greenlighting a "revenue is up" narrative in any
monthly review, cross-check repeat purchase rate and month-1 cohort
retention in the same period. If revenue rises while repeat rate falls,
the growth is acquisition-driven and fragile, not habit-driven.

---

## What I'd Prioritize First (if I could only ship one thing)

The Footwear checkout-stage fit-confidence fix — it's the most concrete,
directly actionable finding with a clear A/B test design and a natural
guardrail metric, and it connects a funnel problem to a returns problem
that likely also carries real logistics cost (reverse shipping, restocking).
It's the kind of fix that shows up in both the conversion funnel *and* the
P&L.
