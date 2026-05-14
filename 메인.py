import streamlit as st
from db_utils import init_routine_if_empty

st.set_page_config(page_title="나의 플래너", page_icon="📅", layout="wide")

init_routine_if_empty()

st.title("📅 나의 플래너")
st.write("### 환영해!")

st.markdown("""
왼쪽 사이드바에서 메뉴를 골라:

- **📝 일간 기록**: 오늘 하루 시간대별로 기록 (지금 시각 빠르게 찍기)
- **📅 주간 보기**: 한 주 전체를 표로 보기 (셀 직접 편집 가능)

📊 분석 기능은 데이터가 좀 쌓이면 추가할 예정이야.
""")

st.write("---")
st.caption("Tip: 사이드바가 안 보이면 왼쪽 위 화살표(>>)를 클릭")