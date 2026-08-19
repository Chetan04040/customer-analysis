# Customer Shopping Behavior Analysis

Two Streamlit dashboards built on a 3,900-row retail order file. One looks at
what sells. The other looks at what the discount programme is costing.

The repo also carries the cleaning notebook and the SQL used for the same
questions against a database copy of the table.


---

## Overview

The dataset records one apparel order per row: who bought, what they bought,
what they paid, how they paid, whether a discount was applied, and the rating
they left afterwards. There is no cost or margin column, so every money figure
here is order value rather than profit. That limit shapes what the second
dashboard can honestly claim, and it is called out on the page itself.

Work order was: clean the file in pandas, answer the business questions in SQL,
then put the two questions worth watching over time into an app.

## What is in the repo

| File | What it does |
| --- | --- |
| `app.py` | The Streamlit app. Both dashboards live here. |
| `customer_shopping_behavior.csv` | Raw order export, 3,900 rows, 18 columns. |
| `Customer_Shopping_Behavior_Analysis.ipynb` | Cleaning and profiling steps in pandas. |
| `customer_behavior_sql_queries.sql` | Ten business questions answered in SQL. |
| `requirements.txt` | The three packages the app needs. |
| `README.md` | This file. |

## The two dashboards

**1. Product and Category Performance**

Answers where the revenue comes from and whether the products earning it are
the ones customers like. Top twelve products by revenue, a category split with
share labels, the seasonal mix, and a scatter of average rating against revenue
so an item that sells well but rates poorly stands out. A sortable product
table sits underneath for anyone who wants the numbers rather than the picture.

**2. Discount Impact**

Answers whether the discount is buying anything. It compares average order
value with and without a discount, ranks products by how often they go out at a
reduced price, breaks the discount rate down by subscription status, loyalty
band and age group, and closes with a short list of products that are both
heavily discounted and rated below the store median.

Both tabs share one set of sidebar filters: season, category, gender and age
group. Change a filter and every number on both pages moves with it.

## Running it

```bash
git clone https://github.com/Chetan04040/customer-analysis.git
cd customer-analysis

pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`. Keep `customer_shopping_behavior.csv`
next to `app.py`; the script looks for it there rather than in whatever folder
you launched from.

Streamlit 1.49 or newer is needed for the `width="stretch"` chart argument. On
an older version, swap those for `use_container_width=True`.

To reproduce the SQL side, load the cleaned frame into Postgres or MySQL with
the `to_sql` cell at the end of the notebook, then run
`customer_behavior_sql_queries.sql` against the resulting `customer` table.

## What the numbers say

Revenue is $233,081 across 3,900 orders, so the average order sits at $59.76.

Clothing takes 44.7% of revenue and Accessories another 31.8%. Outerwear is the
tail at 7.9%. No single product dominates: the top five items together account
for 22% of revenue, which is what you would expect from a catalogue where
every item is priced in the same $20 to $100 band.

The discount finding is the more interesting one. 43% of orders carry a
discount, and those orders average $59.28 against $60.13 for full-price orders.
The discount is not buying a bigger basket. It is about 85 cents smaller.

Splitting by segment shows why the rate is so high. Every single subscriber
order is discounted, all 1,053 of them. Among non-subscribers the rate is
21.9%. So the headline 43% is really a subscription perk applied automatically
plus a much smaller set of genuine promotions. Subscribers are 27.0% of orders
and 26.9% of revenue, and they spend slightly less per order than everyone
else, which makes the perk hard to justify on order value alone.

Ratings sit in a narrow band, 3.62 to 3.86 out of 5, with Gloves and Sandals at
the top and Shirt and Jeans at the bottom. Nothing is broken, but the products
in the watch list at the bottom of the second tab go out at a discount roughly
half the time while rating below the store median. Those are worth a pricing
look before the next campaign.

## Notes on the data

- 37 review ratings were blank. Each is filled with the median rating for its
  category so the rating charts keep a full row count.
- `Promo Code Used` matched `Discount Applied` on every single row, so it is
  dropped during load.
- Column names are lowercased and snake_cased to match the SQL.
- Age groups are quartiles of the age column: 18-31, 32-44, 45-57, 58-70.
- Loyalty bands come from `previous_purchases`: 1 is New, 2 to 10 Returning,
  above 10 Loyal.
- The file has no dates, no cost of goods and no discount amount. Anything
  presented as a trend over time or as margin would be invented, so neither
  appears.

## Licence

MIT.
