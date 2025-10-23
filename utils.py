
import re
from urllib.parse import quote_plus
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

LANGUAGES = {"ko": "한국어", "en": "English"}

def t(lang, ko, en):
    return ko if lang == "ko" else en

SYNONYMS = {
    "고구마": ["스위트포테이토", "sweet potato"],
    "감자": ["potato", "알감자"],
    "두부": ["tofu"],
    "대파": ["파", "spring onion", "scallion", "green onion"],
    "양파": ["onion"],
    "돼지고기": ["pork"],
    "소고기": ["beef"],
    "닭고기": ["chicken"],
    "계란": ["달걀", "egg", "eggs"],
    "김치": ["kimchi"],
    "애호박": ["주키니", "zucchini"],
    "가지": ["eggplant", "aubergine"],
    "당근": ["carrot"],
    "참치캔": ["통조림참치", "canned tuna", "tuna"],
    "쌀": ["rice"],
    "밀가루": ["flour"],
    "빵가루": ["bread crumbs", "panko"],
    "버터": ["butter"],
    "우유": ["milk"],
    "치즈": ["cheese"],
    "요거트": ["yogurt"],
    "땅콩": ["peanut", "peanuts"],
    "호두": ["walnut", "walnuts"],
    "아몬드": ["almond", "almonds"],
    "대두": ["soy", "soybean", "soy beans"],
    "새우": ["shrimp"],
    "홍합": ["mussel", "mussels"],
    "게": ["crab"],
    "조개": ["clam", "clams"],
}

SUBSTITUTIONS = {
    "우유": ["두유", "오트밀크", "물+가루분유"],
    "버터": ["식용유", "올리브유", "마가린"],
    "밀가루": ["쌀가루", "아몬드가루", "옥수수가루"],
    "치즈": ["영양효모", "두부"],
    "계란": ["두부", "치아씨드젤", "아쿠아파바"],
    "대두": ["두유", "두부"],
    "새우": ["오징어", "닭가슴살"],
}

ALLERGEN_MAP = {
    "gluten": ["밀가루", "빵가루", "파스타", "라면", "맥주"],
    "dairy": ["우유", "버터", "치즈", "요거트"],
    "nuts": ["아몬드", "호두", "땅콩", "캐슈넛", "피스타치오"],
    "shellfish": ["새우", "홍합", "게", "조개", "전복", "랍스터"],
    "egg": ["계란", "달걀", "메추리알"],
    "soy": ["대두", "두유", "두부", "간장"],
}

def normalize_ingredient(name: str):
    s = name.strip().lower()
    s = re.sub(r"\s*\(.*?만료.*?\)", "", s)
    return s

def expand_synonyms(ing_list):
    expanded = set()
    for ing in ing_list:
        ing_l = ing.lower()
        expanded.add(ing_l)
        for k, vals in SYNONYMS.items():
            lowvals = [v.lower() for v in vals]
            if ing_l == k or ing_l in lowvals:
                expanded.add(k)
                expanded.update(lowvals)
    return list(expanded)

def detect_expiring_tokens(text):
    m = re.findall(r"([^,]+?)\(([^)]+)만료\)", text)
    expiring = []
    for ing, token in m:
        ing = ing.strip()
        token = token.strip()
        now = datetime.now()
        due = None
        if token in ["오늘", "today"]:
            due = now.date()
        elif token in ["내일", "tomorrow"]:
            due = (now + timedelta(days=1)).date()
        else:
            try:
                due = datetime.fromisoformat(token).date()
            except:
                pass
        expiring.append((ing, due))
    return expiring

def violates_allergy(ingredients, allergy_flags):
    for key, on in allergy_flags.items():
        if not on:
            continue
        for bad in ALLERGEN_MAP.get(key, []):
            for ing in ingredients:
                if bad.lower() in ing.lower():
                    return True
    return False

NUTRIENTS = {
    "두부": (76, 8, 4.8, 1.9, 7),
    "닭가슴살": (165, 31, 3.6, 0, 74),
    "계란": (155, 13, 11, 1.1, 124),
    "쌀": (130, 2.4, 0.3, 28.7, 1),
    "김치": (23, 1.1, 0.2, 4.1, 498),
    "돼지고기": (242, 27, 14, 0, 62),
    "소고기": (250, 26, 15, 0, 72),
    "감자": (77, 2, 0.1, 17, 6),
    "고구마": (86, 1.6, 0.1, 20, 55),
    "양파": (40, 1.1, 0.1, 9.3, 4),
    "당근": (41, 0.9, 0.2, 9.6, 69),
    "대파": (31, 1.8, 0.2, 7.6, 20),
    "애호박": (17, 1.2, 0.3, 3.1, 8),
    "가지": (25, 1, 0.2, 6, 2),
    "우유": (60, 3.2, 3.3, 4.8, 44),
    "치즈": (402, 25, 33, 1.3, 621),
    "버터": (717, 0.9, 81, 0.1, 11),
    "밀가루": (364, 10, 1, 76, 2),
    "대두": (446, 36, 20, 30, 2),
    "새우": (99, 24, 0.3, 0.2, 111),
}

def sum_nutrition(ingredients_with_grams):
    kcal=prot=fat=carb=sodium=0.0
    for name, g in ingredients_with_grams:
        base = NUTRIENTS.get(name, None)
        if not base:
            continue
        mult = (g or 0)/100.0
        k,p,f,c,s = base
        kcal += k*mult; prot += p*mult; fat += f*mult; carb += c*mult; sodium += s*mult
    return {
        "kcal": round(kcal,1),
        "protein": round(prot,1),
        "fat": round(fat,1),
        "carbs": round(carb,1),
        "sodium": round(sodium,1),
    }

def spotify_search_link(query):
    return f"https://open.spotify.com/search/{quote_plus(query)}"

def youtube_search_link(query):
    return f"https://www.youtube.com/results?search_query={quote_plus(query)}"

def to_markdown_card(lang, recipe):
    lines = []
    if lang == "ko":
        lines.append(f"# {recipe['name_ko']}")
        lines.append(f"- 카테고리: {recipe.get('category','')}")
        lines.append(f"- 난이도: {recipe.get('difficulty','보통')}")
        lines.append(f"- 1인분 영양: {recipe['kcal']} kcal / P{recipe['protein']}g / F{recipe['fat']}g / C{recipe['carbs']}g")
        lines.append("\n## 재료")
        for ing in recipe["ingredients"]:
            lines.append(f"- {ing}")
        lines.append("\n## 만드는 법")
        for i, step in enumerate(recipe["steps"], 1):
            lines.append(f"{i}. {step}")
        if recipe.get("benefits"):
            lines.append("\n## 효능")
            lines.append(f"- {recipe['benefits']}")
    else:
        lines.append(f"# {recipe['name_en']}")
        lines.append(f"- Category: {recipe.get('category','')}")
        lines.append(f"- Difficulty: {recipe.get('difficulty','Medium')}")
        lines.append(f"- Per serving: {recipe['kcal']} kcal / P{recipe['protein']}g / F{recipe['fat']}g / C{recipe['carbs']}g")
        lines.append("\n## Ingredients")
        for ing in recipe["ingredients_en"]:
            lines.append(f"- {ing}")
        lines.append("\n## Steps")
        for i, step in enumerate(recipe["steps_en"], 1):
            lines.append(f"{i}. {step}")
        if recipe.get("benefits_en"):
            lines.append("\n## Benefits")
            lines.append(f"- {recipe['benefits_en']}")
    return "\n".join(lines)
