import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
import io

# For PDP scraping
import requests
from bs4 import BeautifulSoup

st.sidebar.header("Product Info & Filters")
entry_method = st.sidebar.radio(
    "How would you like to input product info?",
    ("Paste Product Title", "Paste Product PDP Link (Amazon)")
)

if entry_method == "Paste Product Title":
    product_title = st.sidebar.text_input(
        "Product Title *required*",
        "",
    )
else:
    pdp_link = st.sidebar.text_input("Amazon PDP Link (e.g. https://www.amazon.com/dp/XXX)")
    product_title = ""
    if pdp_link:
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            resp = requests.get(pdp_link, headers=headers, timeout=8)
            soup = BeautifulSoup(resp.text, "html.parser")
            title_tag = soup.find('span', id='productTitle')
            if title_tag:
                product_title = title_tag.get_text(strip=True)
                st.sidebar.success(f"Product title found: {product_title[:80]}{'...' if len(product_title)>80 else ''}")
            else:
                st.sidebar.error("Could not extract product title! Paste title manually instead.")
        except Exception as e:
            st.sidebar.error(f"Failed to load product page: {e}. Paste title manually if needed.")

product_item_type = st.sidebar.text_input("Item Type (capsule, gummy, etc.)", "capsule")
search_volume_min = st.sidebar.number_input("Minimum Search Volume", value=200, min_value=0, max_value=100000)
threshold = st.sidebar.slider("Title Similarity Threshold (lower=wider match)", 0, 100, 55)

exclude_types = [
    "gummy", "gummies", "tablet", "tablets", "powder", "softgel", "softgels",
    "liquid", "drops", "chewable", "chewables", "spray", "patch", "syrup"
]
exclude_types = [x for x in exclude_types if x not in [product_item_type, product_item_type + 's']]

st.title("Amazon Keyword Relevance Filter (Helium 10 Style)")

uploaded_file = st.file_uploader("Upload Helium 10 CSV or Excel", type=['csv', 'xlsx'])

if uploaded_file and product_title:
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

        # Download link (BytesIO buffer method)
        output = io.BytesIO()
        out_df.to_excel(output, index=False, engine='openpyxl')
        st.download_button(
            label="Download results as Excel",
            data=output.getvalue(),
            file_name="relevant_keywords.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
elif not product_title and uploaded_file:
    st.info("Provide a product title (or valid PDP link) in the sidebar.")

else:
    st.info("Paste your product title or PDP link in the sidebar AND upload a Helium 10 XLSX/CSV to get started.")
