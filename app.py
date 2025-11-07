import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz

# --- Sidebar Settings ---
st.sidebar.header("Product Info & Filters")
product_title = st.sidebar.text_input(
    "Product Title",
    "Protocol EGCg 200 mg - 200 mg EGCg Green Tea Extract - Phytonutrients & Polyphenols Supplement* - Kosher & Vegan - 90 Veg Capsules")
product_item_type = st.sidebar.text_input("Item Type (e.g., capsule, gummy, tablet)", "capsule")
search_volume_min = st.sidebar.number_input("Minimum Search Volume", value=200, min_value=0, max_value=100000)
threshold = st.sidebar.slider("Title Similarity Threshold (lower=wider match)", 0, 100, 55)

exclude_types = [
    "gummy", "gummies", "tablet", "tablets", "powder", "softgel", "softgels",
    "liquid", "drops", "chewable", "chewables", "spray", "patch", "syrup"
]
exclude_types = [x for x in exclude_types if x not in [product_item_type, product_item_type + 's']]

st.title("Amazon Keyword Relevance Filter (Helium 10 Style)")

# --- Upload & Process ---
uploaded_file = st.file_uploader("Upload Helium 10 CSV or Excel", type=['csv', 'xlsx'])

if uploaded_file:
    # Load file
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Identify columns
    cols = [c.lower().strip() for c in df.columns]
    kw_col = next((df.columns[i] for i, c in enumerate(cols) if 'keyword' in c), df.columns[0])
    sv_col = next((df.columns[i] for i, c in enumerate(cols) if 'search' in c and 'volume' in c), None)

    if not sv_col:
        st.error("Search Volume column not found! Please check your file.")
    else:
        keyword_phrases = df[kw_col].astype(str).str.strip().tolist()
        search_volumes = df[sv_col].fillna(0).astype(int).tolist()
        product_title_lower = product_title.lower()

        # Filter
        filtered_kws = []
        filtered_sv = []
        for kw, sv in zip(keyword_phrases, search_volumes):
            kw_lower = kw.lower()
            if sv > search_volume_min:
                if product_item_type in kw_lower or all(x not in kw_lower for x in exclude_types):
                    score_title = fuzz.partial_ratio(kw_lower, product_title_lower)
                    if score_title >= threshold:
                        filtered_kws.append(kw)
                        filtered_sv.append(sv)

        out_df = pd.DataFrame({"Keyword Phrase": filtered_kws, "Search Volume": filtered_sv})

        st.write(f"**{len(out_df)} relevant keywords found.**")
        st.dataframe(out_df)

        # Download link
        st.download_button(
            label="Download results as Excel",
            data=out_df.to_excel(index=False, engine='openpyxl'),
            file_name="relevant_keywords.xlsx"
        )
else:
    st.info("Upload a Helium 10 CSV or XLSX to get started.")