
import random, csv
from pathlib import Path

KR_METHODS = ["볶음", "구이", "조림", "찜", "전", "수프", "비빔", "덮밥", "샐러드", "파스타"]
EN_METHODS = ["Stir-fry", "Grilled", "Braised", "Steamed", "Pancake", "Soup", "Mixed", "Rice bowl", "Salad", "Pasta"]
BASES = [
    ("두부", "Tofu"), ("닭가슴살", "Chicken breast"), ("소고기", "Beef"), ("돼지고기", "Pork"),
    ("감자", "Potato"), ("고구마", "Sweet potato"), ("양파", "Onion"), ("당근", "Carrot"),
    ("가지", "Eggplant"), ("애호박", "Zucchini"), ("참치캔","Canned tuna"), ("쌀", "Rice"),
    ("김치","Kimchi"), ("계란","Egg"),
]
EXTRAS = [
    ("대파","Green onion"), ("마늘","Garlic"), ("버섯","Mushroom"), ("피망","Bell pepper"), ("브로콜리","Broccoli"),
    ("우유","Milk"), ("치즈","Cheese"), ("버터","Butter"), ("밀가루","Flour"), ("대두","Soy"),
    ("새우","Shrimp")
]

def est_macros(main_ko):
    if main_ko in ["닭가슴살","소고기","돼지고기","새우","참치캔"]:
        return 420, 35, 16, 20
    if main_ko in ["두부","계란"]:
        return 350, 25, 20, 18
    if main_ko in ["쌀","감자","고구마","파스타"]:
        return 520, 12, 10, 85
    return 300, 8, 8, 35

def build_row(i):
    m = random.randrange(len(KR_METHODS))
    method_kr, method_en = KR_METHODS[m], EN_METHODS[m]
    (base_kr, base_en) = random.choice(BASES)
    extras = random.sample(EXTRAS, k=random.randint(1,3))
    ing_kr = [base_kr] + [e[0] for e in extras]
    ing_en = [base_en] + [e[1] for e in extras]
    name_ko = f"{base_kr} {method_kr}"
    name_en = f"{method_en} {base_en}"
    kcal, p, f, c = est_macros(base_kr)
    steps_ko = [f"{base_kr}와 재료를 손질한다.", "달군 팬에 기름을 두른다.", "센불에 볶다가 간을 맞춘다.", "접시에 담아낸다."]
    steps_en = [f"Prep {base_en} and other ingredients.", "Heat oil in a pan.", "Stir-fry on high and season.", "Plate and serve."]
    benefits_ko = "단백질 보충과 포만감에 도움."
    benefits_en = "Helps with protein intake and satiety."
    return {
        "id": i,
        "name_ko": name_ko,
        "name_en": name_en,
        "category": "메인",
        "difficulty": "보통",
        "ingredients": "|".join(ing_kr),
        "ingredients_en": "|".join(ing_en),
        "steps": "|".join(steps_ko),
        "steps_en": "|".join(steps_en),
        "kcal": kcal, "protein": p, "fat": f, "carbs": c,
        "benefits": benefits_ko, "benefits_en": benefits_en
    }

def main():
    random.seed(42)
    rows = [build_row(i) for i in range(1, 650)]
    path = Path(__file__).parent / "data" / "recipes.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Wrote {path} with {len(rows)} recipes.")

if __name__ == "__main__":
    main()
