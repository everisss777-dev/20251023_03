
# FridgeChef (냉장고 파먹기)

Streamlit 앱: 냉장고에 있는 식재료를 입력하면 만들 수 있는 요리를 추천하고, 3끼 식단을 자동으로 구성합니다.
한국어/영어 듀얼 UI, 알레르기 필터, 즐겨찾기, 레시피 카드(.md) 다운로드, 임박 재료 인식, 영양소 계산,
추천 음악 링크, 공유용 쿼리스트링 등을 포함합니다.

## 빠른 시작
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 데이터 생성
```bash
python recipes_generator.py
```
600개 이상 레시피가 `data/recipes.csv`로 생성됩니다.

## 배포 (GitHub → Streamlit Community Cloud)
1) GitHub 새 저장소 생성 후 이 폴더 전체 업로드
2) Streamlit Community Cloud에서 New app → 저장소/브랜치/파일(app.py) 선택 → Deploy

## GitHub Actions (CI)
- 푸시/PR 시 의존성 설치, flake8 문법 점검, 데이터셋 500+ 행 스모크테스트 수행

## 라이선스
MIT
