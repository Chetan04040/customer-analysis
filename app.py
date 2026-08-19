"""
Customer Shopping Behavior - Streamlit dashboard.

Two dashboards on one dataset:
  1. Product and Category Performance - what sells, what earns, what people rate well.
  2. Discount Impact - who gets discounts, what they cost, and whether they pay off.

Run with:  streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Sit next to the CSV rather than trusting the working directory, so the app
# starts the same way from any folder.
DATA_FILE = Path(__file__).parent / "customer_shopping_behavior.csv"

# Categorical slots, fixed order. Never cycled, never reassigned by rank.
SLOT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
BLUE_RAMP = ["#cfe2f7", "#9cc4ee", "#6aa5e2", "#3f8bd9", "#2a78d6", "#1c5aa3"]
# Category keeps its hue everywhere, so a filter never repaints the survivors.
CATEGORY_COLOR = {
    "Clothing": SLOT[0],
    "Accessories": SLOT[1],
    "Footwear": SLOT[2],
    "Outerwear": SLOT[3],
}
INK = "#0b0b0b"
MUTED = "#52514e"
GRID = "#e6e5e1"

st.set_page_config(page_title="Customer Shopping Behavior", layout="wide")


# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------
@st.cache_data
def load_data(path: Path = DATA_FILE) -> pd.DataFrame:
    """Read the raw export and apply the same cleaning used in the notebook."""
    if not Path(path).exists():
        st.error(
            f"Could not find {Path(path).name}. Keep the CSV in the same folder "
            "as app.py."
        )
        st.stop()
    frame = pd.read_csv(path)

    frame.columns = frame.columns.str.lower().str.replace(" ", "_")
    frame = frame.rename(columns={"purchase_amount_(usd)": "purchase_amount"})

    # 37 ratings are blank. Fill each with the median rating of its category
    # so the product-rating chart keeps a full row count.
    frame["review_rating"] = frame.groupby("category")["review_rating"].transform(
        lambda col: col.fillna(col.median())
    )

    # promo_code_used repeats discount_applied value for value, so it goes.
    if "promo_code_used" in frame.columns:
        frame = frame.drop(columns="promo_code_used")

    frame["age_group"] = pd.qcut(
        frame["age"], q=4, labels=["18-31", "32-44", "45-57", "58-70"]
    )

    days_between_orders = {
        "Weekly": 7,
        "Bi-Weekly": 14,
        "Fortnightly": 14,
        "Monthly": 30,
        "Quarterly": 90,
        "Every 3 Months": 90,
        "Annually": 365,
    }
    frame["purchase_frequency_days"] = frame["frequency_of_purchases"].map(
        days_between_orders
    )

    frame["loyalty_band"] = pd.cut(
        frame["previous_purchases"],
        bins=[0, 1, 10, frame["previous_purchases"].max()],
        labels=["New", "Returning", "Loyal"],
    )
    frame["discounted"] = frame["discount_applied"].eq("Yes")
    return frame


def style(fig: go.Figure, height: int = 360) -> go.Figure:
    """One place for the chart furniture, so every figure matches."""
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=48, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=13, color=INK),
        title=dict(font=dict(size=15, color=INK), x=0, xanchor="left"),
        legend=dict(
            orientation="h", y=-0.18, x=0, title_text="", font=dict(color=MUTED)
        ),
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=GRID, font_size=12),
        bargap=0.28,
    )
    fig.update_xaxes(
        showgrid=False, linecolor=GRID, tickfont=dict(color=MUTED), title_font_size=12
    )
    fig.update_yaxes(
        gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED), title_font_size=12
    )
    return fig


def headroom(fig: go.Figure, values, axis: str = "x", pad: float = 0.18) -> go.Figure:
    """Leave room past the longest bar so the end label is not clipped."""
    top = float(max(values)) * (1 + pad) if len(values) else 1.0
    if axis == "x":
        fig.update_xaxes(range=[0, top])
    else:
        fig.update_yaxes(range=[0, top])
    return fig


def money(value: float) -> str:
    return f"${value:,.0f}"


def money_exact(value: float) -> str:
    """Two decimals, with the sign outside the currency symbol."""
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


df = load_data()

# ----------------------------------------------------------------------
# Filters
# ----------------------------------------------------------------------
st.sidebar.header("Filters")

seasons = st.sidebar.multiselect(
    "Season", sorted(df["season"].unique()), default=sorted(df["season"].unique())
)
categories = st.sidebar.multiselect(
    "Category", sorted(df["category"].unique()), default=sorted(df["category"].unique())
)
genders = st.sidebar.multiselect(
    "Gender", sorted(df["gender"].unique()), default=sorted(df["gender"].unique())
)
age_bands = st.sidebar.multiselect(
    "Age group",
    list(df["age_group"].cat.categories),
    default=list(df["age_group"].cat.categories),
)

data = df[
    df["season"].isin(seasons)
    & df["category"].isin(categories)
    & df["gender"].isin(genders)
    & df["age_group"].isin(age_bands)
]

st.sidebar.caption(f"{len(data):,} of {len(df):,} orders in view")

st.title("Customer Shopping Behavior")
st.caption(
    "3,900 orders from a US apparel retailer. Use the sidebar to narrow the view; "
    "both dashboards react to the same filters."
)

if data.empty:
    st.warning("No orders match those filters. Widen the selection to carry on.")
    st.stop()

tab_products, tab_discounts = st.tabs(
    ["Product and Category Performance", "Discount Impact"]
)

# ======================================================================
# Dashboard 1 - Product and Category Performance
# ======================================================================
with tab_products:
    st.subheader("Which products carry the business")
    st.caption(
        "Question: where does revenue actually come from, and do the top sellers "
        "keep customers happy?"
    )

    left, mid, right, far = st.columns(4)
    left.metric("Revenue", money(data["purchase_amount"].sum()))
    mid.metric("Orders", f"{len(data):,}")
    right.metric("Average order", money_exact(data["purchase_amount"].mean()))
    far.metric("Average rating", f"{data['review_rating'].mean():.2f} / 5")

    st.divider()

    col_a, col_b = st.columns([3, 2])

    with col_a:
        by_item = (
            data.groupby("item_purchased")
            .agg(
                revenue=("purchase_amount", "sum"),
                orders=("customer_id", "count"),
                rating=("review_rating", "mean"),
            )
            .sort_values("revenue", ascending=False)
            .head(12)
            .reset_index()
        )
        fig = px.bar(
            by_item.sort_values("revenue"),
            x="revenue",
            y="item_purchased",
            orientation="h",
            title="Top 12 products by revenue",
            color="revenue",
            color_continuous_scale=BLUE_RAMP,
            custom_data=["orders", "rating"],
        )
        fig.update_traces(
            marker_line_width=0,
            hovertemplate=(
                "<b>%{y}</b><br>Revenue $%{x:,.0f}"
                "<br>Orders %{customdata[0]:,}"
                "<br>Rating %{customdata[1]:.2f}<extra></extra>"
            ),
            texttemplate="$%{x:,.0f}",
            textposition="outside",
            textfont=dict(color=MUTED, size=11),
        )
        fig.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title="")
        headroom(fig, by_item["revenue"])
        st.plotly_chart(style(fig, 470), width="stretch")

    with col_b:
        by_category = (
            data.groupby("category")
            .agg(
                revenue=("purchase_amount", "sum"),
                orders=("customer_id", "count"),
                average=("purchase_amount", "mean"),
            )
            .sort_values("revenue", ascending=False)
            .reset_index()
        )
        by_category["share"] = (
            by_category["revenue"] / by_category["revenue"].sum()
        )
        fig = px.bar(
            by_category,
            x="category",
            y="revenue",
            title="Revenue by category, with share of the total",
            color="category",
            color_discrete_map=CATEGORY_COLOR,
            text="share",
            custom_data=["orders", "average"],
        )
        fig.update_traces(
            marker_line_width=0,
            texttemplate="%{text:.0%}",
            textposition="outside",
            textfont=dict(color=MUTED, size=11),
            hovertemplate=(
                "<b>%{x}</b><br>Revenue $%{y:,.0f}"
                "<br>Orders %{customdata[0]:,}"
                "<br>Average order $%{customdata[1]:.2f}<extra></extra>"
            ),
        )
        fig.update_layout(
            showlegend=False, xaxis_title="", yaxis_title="", yaxis_tickprefix="$"
        )
        headroom(fig, by_category["revenue"], axis="y", pad=0.12)
        st.plotly_chart(style(fig, 470), width="stretch")

    col_c, col_d = st.columns(2)

    with col_c:
        seasonal = (
            data.groupby(["season", "category"], observed=True)["purchase_amount"]
            .sum()
            .reset_index()
        )
        season_order = [s for s in ["Spring", "Summer", "Fall", "Winter"] if s in seasons]
        fig = px.bar(
            seasonal,
            x="season",
            y="purchase_amount",
            color="category",
            barmode="group",
            title="Seasonal revenue mix",
            color_discrete_map=CATEGORY_COLOR,
            category_orders={"season": season_order},
        )
        fig.update_traces(
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>%{fullData.name}<br>$%{y:,.0f}<extra></extra>",
        )
        fig.update_layout(xaxis_title="", yaxis_title="Revenue", yaxis_tickprefix="$")
        st.plotly_chart(style(fig), width="stretch")

    with col_d:
        rated = (
            data.groupby("item_purchased")
            .agg(
                rating=("review_rating", "mean"),
                revenue=("purchase_amount", "sum"),
                orders=("customer_id", "count"),
            )
            .reset_index()
        )
        fig = px.scatter(
            rated,
            x="rating",
            y="revenue",
            size="orders",
            size_max=20,
            title="Rating against revenue, one dot per product",
            color_discrete_sequence=[SLOT[0]],
            custom_data=["item_purchased", "orders"],
        )
        fig.update_traces(
            marker=dict(line=dict(width=2, color="#fcfcfb"), opacity=0.9),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>Rating %{x:.2f}"
                "<br>Revenue $%{y:,.0f}<br>Orders %{customdata[1]:,}<extra></extra>"
            ),
        )
        fig.add_vline(
            x=rated["rating"].mean(),
            line_dash="dot",
            line_color=MUTED,
            annotation_text="average rating",
            annotation_font_color=MUTED,
            annotation_font_size=11,
        )
        fig.update_layout(
            xaxis_title="Average review rating",
            yaxis_title="Revenue",
            yaxis_tickprefix="$",
        )
        st.plotly_chart(style(fig), width="stretch")

    with st.expander("Product table"):
        table = (
            data.groupby(["category", "item_purchased"])
            .agg(
                orders=("customer_id", "count"),
                revenue=("purchase_amount", "sum"),
                average_order=("purchase_amount", "mean"),
                rating=("review_rating", "mean"),
            )
            .round(2)
            .sort_values("revenue", ascending=False)
            .reset_index()
        )
        st.dataframe(table, width="stretch", hide_index=True)

# ======================================================================
# Dashboard 2 - Discount Impact
# ======================================================================
with tab_discounts:
    st.subheader("What the discount programme is buying")
    st.caption(
        "Question: 43% of orders carry a discount. Are those orders bigger, or is "
        "the retailer paying for sales it would have made anyway?"
    )

    discounted = data[data["discounted"]]
    full_price = data[~data["discounted"]]

    avg_discounted = discounted["purchase_amount"].mean() if len(discounted) else 0.0
    avg_full = full_price["purchase_amount"].mean() if len(full_price) else 0.0
    gap = avg_discounted - avg_full

    one, two, three, four = st.columns(4)
    one.metric("Discounted orders", f"{len(discounted) / len(data):.1%}")
    two.metric("Average discounted order", money_exact(avg_discounted))
    three.metric("Average full-price order", money_exact(avg_full))
    four.metric(
        "Difference",
        money_exact(gap),
        delta=f"{(gap / avg_full):.1%}" if avg_full else None,
    )

    if gap < 0:
        st.info(
            f"Discounted orders come in {money_exact(abs(gap))} smaller than full-price "
            "orders on average. The discount is not buying a bigger basket."
        )

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        by_item = (
            data.groupby("item_purchased")
            .agg(
                rate=("discounted", "mean"),
                orders=("customer_id", "count"),
                revenue=("purchase_amount", "sum"),
            )
            .sort_values("rate", ascending=False)
            .head(12)
            .reset_index()
        )
        fig = px.bar(
            by_item.sort_values("rate"),
            x="rate",
            y="item_purchased",
            orientation="h",
            title="Products most often sold at a discount",
            color="rate",
            color_continuous_scale=BLUE_RAMP,
            custom_data=["orders", "revenue"],
        )
        fig.update_traces(
            marker_line_width=0,
            texttemplate="%{x:.0%}",
            textposition="outside",
            textfont=dict(color=MUTED, size=11),
            hovertemplate=(
                "<b>%{y}</b><br>Discounted on %{x:.1%} of orders"
                "<br>Orders %{customdata[0]:,}"
                "<br>Revenue $%{customdata[1]:,.0f}<extra></extra>"
            ),
        )
        fig.update_layout(
            coloraxis_showscale=False,
            yaxis_title="",
            xaxis_title="",
            xaxis_tickformat=".0%",
        )
        headroom(fig, by_item["rate"], pad=0.12)
        st.plotly_chart(style(fig, 470), width="stretch")

    with col_b:
        basket = (
            data.groupby(["category", "discounted"])["purchase_amount"]
            .mean()
            .reset_index()
        )
        basket["price_type"] = basket["discounted"].map(
            {True: "Discounted", False: "Full price"}
        )
        fig = px.bar(
            basket,
            x="category",
            y="purchase_amount",
            color="price_type",
            barmode="group",
            title="Average order value, discounted against full price",
            color_discrete_sequence=[SLOT[0], SLOT[1]],
            category_orders={"price_type": ["Full price", "Discounted"]},
        )
        fig.update_traces(
            marker_line_width=0,
            texttemplate="$%{y:.0f}",
            textposition="outside",
            textfont=dict(color=MUTED, size=11),
            hovertemplate="<b>%{x}</b><br>%{fullData.name}<br>$%{y:.2f}<extra></extra>",
        )
        fig.update_layout(
            xaxis_title="",
            yaxis_title="Average order value",
            yaxis_tickprefix="$",
        )
        headroom(fig, basket["purchase_amount"], axis="y", pad=0.12)
        st.plotly_chart(style(fig, 470), width="stretch")

    col_c, col_d = st.columns(2)

    with col_c:
        segments = []
        for label, column in [
            ("Subscription", "subscription_status"),
            ("Loyalty", "loyalty_band"),
            ("Age group", "age_group"),
        ]:
            piece = (
                data.groupby(column, observed=True)["discounted"]
                .mean()
                .reset_index(name="rate")
            )
            piece["segment"] = piece[column].astype(str)
            piece["dimension"] = label
            segments.append(piece[["dimension", "segment", "rate"]])
        segment_rates = pd.concat(segments)
        segment_rates["segment"] = segment_rates.apply(
            lambda row: (
                f"Subscriber: {row['segment']}"
                if row["dimension"] == "Subscription"
                else row["segment"]
            ),
            axis=1,
        )

        fig = px.bar(
            segment_rates,
            x="rate",
            y="segment",
            color="dimension",
            orientation="h",
            title="Share of orders discounted, by customer segment",
            color_discrete_sequence=SLOT,
        )
        fig.update_traces(
            marker_line_width=0,
            texttemplate="%{x:.0%}",
            textposition="outside",
            textfont=dict(color=MUTED, size=11),
            hovertemplate="<b>%{y}</b><br>%{x:.1%} of orders discounted<extra></extra>",
        )
        fig.update_layout(
            yaxis_title="",
            xaxis_title="",
            xaxis_tickformat=".0%",
            xaxis_range=[0, 1.12],
            yaxis_autorange="reversed",
        )
        st.plotly_chart(style(fig, 400), width="stretch")

    with col_d:
        seasonal = (
            data.groupby("season")
            .agg(rate=("discounted", "mean"), revenue=("purchase_amount", "sum"))
            .reindex([s for s in ["Spring", "Summer", "Fall", "Winter"] if s in seasons])
            .reset_index()
        )
        fig = px.bar(
            seasonal,
            x="season",
            y="rate",
            title="Discount rate by season",
            color_discrete_sequence=[SLOT[0]],
            custom_data=["revenue"],
        )
        fig.update_traces(
            marker_line_width=0,
            texttemplate="%{y:.0%}",
            textposition="outside",
            textfont=dict(color=MUTED, size=11),
            hovertemplate=(
                "<b>%{x}</b><br>%{y:.1%} of orders discounted"
                "<br>Revenue $%{customdata[0]:,.0f}<extra></extra>"
            ),
        )
        fig.update_layout(xaxis_title="", yaxis_title="", yaxis_tickformat=".0%")
        headroom(fig, seasonal["rate"], axis="y", pad=0.14)
        st.plotly_chart(style(fig, 400), width="stretch")

    st.markdown("**Products to look at first**")
    st.caption(
        "Heavily discounted and rated below the store average. These are the "
        "candidates for a price review rather than another promotion."
    )
    watch = (
        data.groupby("item_purchased")
        .agg(
            discount_rate=("discounted", "mean"),
            rating=("review_rating", "mean"),
            revenue=("purchase_amount", "sum"),
            orders=("customer_id", "count"),
        )
        .reset_index()
    )
    watch = watch[
        (watch["discount_rate"] >= watch["discount_rate"].median())
        & (watch["rating"] <= watch["rating"].median())
    ].sort_values("discount_rate", ascending=False)
    watch["discount_rate"] = watch["discount_rate"].map(lambda v: f"{v:.1%}")
    watch["rating"] = watch["rating"].map(lambda v: f"{v:.2f}")
    watch["revenue"] = watch["revenue"].map(money)

    if watch.empty:
        st.caption("Nothing lands in this bucket under the current filters.")
    else:
        st.dataframe(
            watch.rename(
                columns={
                    "item_purchased": "Product",
                    "discount_rate": "Discounted %",
                    "rating": "Rating",
                    "revenue": "Revenue",
                    "orders": "Orders",
                }
            ),
            width="stretch",
            hide_index=True,
        )

st.divider()
st.caption(
    "Data: customer_shopping_behavior.csv (3,900 rows). The file records whether a "
    "discount was applied but not its size or the cost of goods, so margin figures "
    "here are read from order value, not from profit."
)
