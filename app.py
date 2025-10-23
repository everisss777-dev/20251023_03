
import io
from urllib.parse import urlencode
import pandas as pd
import streamlit as st

from utils import (
    t, LANGUAGES, expand_synonyms, normalize_ingredient, detect_expiring_tokens,
    violates_allergy, sum_nutrition, spotify_search_link, youtube_search_link, to_markdown_card
)

APP_TITLE = "냉장고 파먹기 • FridgeChef"

def init_state():
    qp = st.query_params
    if "lang" not in st.session_state:
        st.session_state.lang = qp.get("lang", "ko")
    if "favorites" not in st.session_state:
        st.session_state.favorites = set()

def load_data():
    df = pd.read_csv("data/recipes.csv")
    for c in ["ingredients","ingredients_en","steps","steps_en"]:
        df[c] = df[c].fillna("").apply(lambda x: [s.strip() for s in x.split("|") if s.strip()])
    return df

def apply_filters(df, have_ings, allergy, lang):
    if have_ings:
        expanded = set(expand_synonyms([normalize_ingredient(i) for i in have_ings]))
        def match_row(row):
            target = row["ingredients"] if lang=="ko" else row["ingredients_en"]
            score = sum(1 for ing in target if normalize_ingredient(ing) in expanded)
            return score
        df = df.assign(_score=df.apply(match_row, axis=1)).query("_score>0").sort_values("_score", ascending=False)
    def allergen_ok(row):
        flags = {k: allergy.get(k, False) for k in ["gluten","dairy","nuts","shellfish","egg","soy"]}
        return not violates_allergy(row["ingredients"], flags)
    df = df[df.apply(allergen_ok, axis=1)]
    return df

def build_shopping_list(have_ings, chosen):
    have = {normalize_ingredient(x) for x in have_ings}
    need_ko, need_en = {}, {}
    for r in chosen:
        for ing_ko, ing_en in zip(r["ingredients"], r["ingredients_en"]):
            key = normalize_ingredient(ing_ko)
            if key not in have:
                need_ko[ing_ko] = need_ko.get(ing_ko, 0) + 1
                need_en[ing_en] = need_en.get(ing_en, 0) + 1
    return list(need_ko.keys()), list(need_en.keys())

def pick_best_three(df, have_ings):
    have = set([normalize_ingredient(i) for i in have_ings])
    chosen = []
    remaining = df.copy()
    for _ in range(3):
        if remaining.empty:
            break
        def coverage(row):
            return len({normalize_ingredient(x) for x in row["ingredients"]} & have)
        remaining = remaining.assign(_cov=remaining.apply(coverage, axis=1)).sort_values("_cov", ascending=False)
        top = remaining.iloc[0]
        chosen.append(top)
        remaining = remaining.iloc[1:]
    return chosen

def recipe_card(recipe, lang, section_key=""):
    with st.container(border=True):
        name = recipe["name_ko"] if lang=="ko" else recipe["name_en"]
        st.subheader(name)
        st.caption(f"{recipe['kcal']} kcal • P{recipe['protein']} • F{recipe['fat']} • C{recipe['carbs']}")

        cols = st.columns(2)
        with cols[0]:
            st.markdown("**"+t(lang, "재료", "Ingredients")+"**")
            items = recipe["ingredients"] if lang=="ko" else recipe["ingredients_en"]
            st.write(", ".join(items))
            st.markdown("**"+t(lang, "효능", "Benefits")+"**")
            st.write(recipe["benefits"] if lang=="ko" else recipe["benefits_en"])
        with cols[1]:
            st.markdown("**"+t(lang, "만드는 법", "Steps")+"**")
            steps = recipe["steps"] if lang=="ko" else recipe["steps_en"]
            st.write("\n".join([f"{i+1}. {s}" for i,s in enumerate(steps)]))

        fid = int(recipe["id"])
        fav_on = fid in st.session_state.favorites
        if st.toggle(t(lang, "즐겨찾기", "Favorite"), value=fav_on, key=f"fav_{section_key}_{fid}"):
            st.session_state.favorites.add(fid)
        else:
            st.session_state.favorites.discard(fid)

        md = to_markdown_card(lang, recipe)
        st.download_button(
            label=t(lang, "요리카드(.md) 다운로드", "Download recipe card (.md)"),
            data=md.encode("utf-8"),
            file_name=(recipe["name_ko"] if lang=="ko" else recipe["name_en"]) + ".md",
            mime="text/markdown",
        )

def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_state()
    lang = st.sidebar.selectbox("Language / 언어", options=list(LANGUAGES.keys()),
                                format_func=lambda k: LANGUAGES[k], index=0 if st.session_state.lang=="ko" else 1)
    st.session_state.lang = lang

    st.sidebar.markdown("### 🔗 " + t(lang, "공유 링크 만들기", "Create share link"))

    st.title(APP_TITLE)

    st.markdown("### 🧺 " + t(lang, "냉장고 재료 입력", "Enter your fridge/pantry"))
    have_text = st.text_input(t(lang, "쉼표(,)로 구분. 예: 두부(내일 만료), 대파, 김치", "Comma-separated. e.g. Tofu(expires tomorrow), Onion, Kimchi"))
    expiring = detect_expiring_tokens(have_text)
    if expiring:
        st.info(t(lang, "임박 재료:", "Expiring soon: ") + ", ".join([f"{a}({b})" for a,b in expiring]))

    have_list = [s.strip() for s in have_text.split(",") if s.strip()]
    have_multi = st.multiselect(t(lang, "보유 재료 멀티셀렉트", "Multi-select your ingredients"), options=have_list, default=have_list)

    st.markdown("### 🚫 " + t(lang, "알레르기 제외", "Exclude allergens"))
    allergy = {
        "gluten": st.checkbox("Gluten(글루텐)"),
        "dairy": st.checkbox("Dairy(유제품)"),
        "nuts": st.checkbox("Nuts(견과)"),
        "shellfish": st.checkbox("Shellfish(갑각류)"),
        "egg": st.checkbox("Egg(난류)"),
        "soy": st.checkbox("Soy(대두)"),
    }

    df = load_data()
    filtered = apply_filters(df, have_multi, allergy, lang)

    st.markdown("### 🍱 " + t(lang, "3끼 자동 구성 (재료 소진 우선)", "Auto 3-meal plan (maximize using your items)"))
    top3 = pick_best_three(filtered if not filtered.empty else df.head(100), have_multi)
    if top3:
        cols = st.columns(len(top3))
        chosen = []
        section_key = "top3"
        for c, row in zip(cols, top3):
            with c:
                recipe_card(row, lang, section_key)
                chosen.append(row)
        miss_ko, miss_en = build_shopping_list(have_multi, chosen)
        with st.expander("🛒 " + t(lang, "부족한 재료 장보기 리스트", "Shopping list for missing items")):
            st.write("**KR**: " + (", ".join(miss_ko) if miss_ko else t(lang, "없음", "None")))
            st.write("**EN**: " + (", ".join(miss_en) if miss_en else "None"))

    st.markdown("### 📚 " + t(lang, "추천 레시피", "Recommended recipes"))
    max_show = st.slider(t(lang, "표시 개수", "Show count"), 5, 50, 12)
    section_key = "results"
    for _, row in filtered.head(max_show).iterrows():
        recipe_card(row, lang, section_key)

    st.markdown("### ⭐ " + t(lang, "즐겨찾기", "Favorites"))
    fav_ids = list(st.session_state.favorites)
    if not fav_ids:
        st.write(t(lang, "즐겨찾기가 비어 있습니다.", "No favorites yet."))
    else:
        fav_df = df[df["id"].isin(fav_ids)]
        section_key = "favs"
        for _, row in fav_df.iterrows():
            recipe_card(row, lang, section_key)

    st.markdown("### 🧮 " + t(lang, "영양소 계산기", "Nutrition calculator"))
    with st.form("nutri"):
        st.write(t(lang, "재료와 중량(그램) 입력", "Enter ingredients and grams"))
        ing1 = st.text_input(t(lang, "재료 1", "Ingredient 1"))
        g1 = st.number_input("g1", min_value=0, value=100)
        ing2 = st.text_input(t(lang, "재료 2", "Ingredient 2"))
        g2 = st.number_input("g2", min_value=0, value=0)
        ing3 = st.text_input(t(lang, "재료 3", "Ingredient 3"))
        g3 = st.number_input("g3", min_value=0, value=0)
        submitted = st.form_submit_button(t(lang, "계산", "Calculate"))
        if submitted:
            items = [(ing1, g1), (ing2, g2), (ing3, g3)]
            res = sum_nutrition(items)
            st.write(res)

    st.markdown("### 🎵 " + t(lang, "요리할 때 들을 음악", "Music to cook with"))
    mood = st.selectbox(t(lang, "무드 선택", "Choose a mood"), ["chill", "energy", "focus", "retro", "k-pop", "lofi"])
    st.write(f"[Spotify]({spotify_search_link(mood+' cooking playlist')}) | [YouTube]({youtube_search_link(mood+' cooking playlist')})")

    params = {"lang": lang, "have": ",".join(have_list),
              "allergy": ",".join(k for k,v in allergy.items() if v), "mood": mood}
    st.sidebar.code("?" + urlencode(params, doseq=True))
    st.sidebar.caption(t(lang, "사이드바 링크를 복사해 공유하세요.", "Copy the sidebar link to share."))

if __name__ == "__main__":
    main()
