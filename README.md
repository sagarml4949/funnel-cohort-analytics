# E-commerce Funnel & Cohort Analytics Dashboard

**A data-driven product analytics project built to demonstrate how a Product
Manager should read funnel drop-off, retention cohorts, and channel ROI —
and turn them into a prioritized next-sprint decision.**

Built with a fashion e-commerce use case in mind (categories, funnel stages,
and metrics modeled on platforms like Myntra).

---

## 1. Problem Framing

E-commerce PMs are constantly asked three questions:
1. **Where in the funnel are we losing users, and why?**
2. **Are the users we acquire actually sticking around (retention), or just
   converting once?**
3. **Is our acquisition spend efficient — which channels deserve more budget?**

This project builds the full pipeline — synthetic data generation → ETL →
interactive dashboard — needed to answer all three with real numbers, then
closes with a PM-style prioritization of what to build/fix next.

## 2. Architecture

```
project1-funnel-cohort-analytics/
├── data/
│   ├── generate_data.py       # synthesizes realistic user/event/spend data
│   ├── users.csv               # generated: 8,000 users with signup cohort, channel, region
│   ├── raw_events.csv          # generated: ~40K funnel events (view/cart/checkout/purchase)
│   ├── marketing_spend.csv     # generated: monthly spend by acquisition channel
│   └── processed/              # ETL output (5 analysis-ready tables)
├── etl/
│   └── etl_pipeline.py         # raw events -> funnel, cohort, KPI, channel tables
├── dashboard/
│   └── app.py                  # Streamlit dashboard (funnel viz, cohort heatmap, ROI, KPIs)
├── insights/
│   └── summary.md              # written analysis + prioritized recommendations
├── deploy/
│   └── deploy_github.py        # publishes to GitHub via REST API (no git install needed)
├── DEPLOYMENT.md               # hosting steps (Streamlit Cloud / HF Spaces / Render)
└── requirements.txt
```

**Why this structure:** it mirrors a real analytics stack — a raw data layer,
a transformation layer, and a presentation layer — rather than one monolithic
notebook. This is deliberate: it's the same separation of concerns a PM would
expect from a data team, and it's easy to swap `data/*.csv` for a real
warehouse export without touching the ETL or dashboard code.

## 3. How to Run

```bash
pip install -r requirements.txt

# 1. Generate the synthetic dataset (~15s)
python data/generate_data.py

# 2. Run the ETL pipeline to build analysis tables
python etl/etl_pipeline.py

# 3. Launch the dashboard
streamlit run dashboard/app.py
```

### Deploy it

`DEPLOYMENT.md` has full hosting instructions (Streamlit Community Cloud,
Hugging Face Spaces, Render). The fastest path needs no Git installation:

```bash
# publish to GitHub through the REST API (token from github.com/settings/tokens)
python deploy/deploy_github.py --repo funnel-cohort-analytics --token ghp_xxx
```

Then open **share.streamlit.io** → *New app* → pick the repo → set the main file
path to `dashboard/app.py` → **Deploy**.

## 4. What the Dataset Models

- **8,000 users** across 4 regions, 3 devices, 5 acquisition channels, signing
  up throughout 2025 (for cohort analysis).
- **~40,000 funnel events** (view → add_to_cart → checkout → purchase) across
  6 fashion categories, each with category-specific conversion and return-rate
  probabilities (e.g., Footwear has the highest return rate — a deliberate nod
  to the size/fit problem explored further in the companion "Size-Fit Product
  Sense" project).
- **Monthly marketing spend** by channel, enabling CAC and ROI calculations.

All data is synthetic but calibrated to realistic e-commerce benchmarks
(conversion rates, AOV distribution via a gamma distribution, return rates by
category) rather than uniform/random noise — this is what makes the resulting
insights (e.g., "Footwear has the weakest cart→checkout conversion") look and
behave like a real analytics finding rather than an obviously fake pattern.

## 5. Key Metrics Computed

| Table | Metrics |
|---|---|
| `funnel_by_category.csv` | View→Cart, Cart→Checkout, Checkout→Purchase, overall conversion, by category |
| `funnel_by_device.csv` | Same funnel, by device (Mobile App / Mobile Web / Desktop) |
| `cohort_retention.csv` | Monthly signup cohort × months-since-signup retention matrix |
| `monthly_kpis.csv` | Revenue, Orders, AOV, Return Rate, Repeat Purchase Rate, CAC |
| `channel_cac.csv` | CAC, Revenue/User, ROI multiple, by acquisition channel |

## 6. Sample Finding (from this run)

> Footwear converts users into "view" sessions at a normal rate but has the
> **weakest cart→checkout conversion (46.3%)** and the **highest return rate**
> of any category — a strong signal that fit/sizing uncertainty, not price or
> interest, is the blocker. See `insights/summary.md` for the full
> recommendation.

## 7. Why This Project (PM Lens, Not Just DS Lens)

Most analytics projects stop at "here's a chart." This one is structured the
way a PM actually works:
- **Diagnose** (funnel + cohort say *where* the problem is)
- **Hypothesize** (why is that stage/channel underperforming)
- **Prioritize** (what's the highest-leverage fix, and what's the guardrail
  metric to watch if we ship it)

That loop — not the Streamlit code — is the actual deliverable.
