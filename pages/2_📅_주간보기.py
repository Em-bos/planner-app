import streamlit as st
import pandas as pd
from datetime import date, timedelta
from db_utils import (
    init_routine_if_empty, get_routine, load_range, save_record
)

st.set_page_config(page_title="주간 보기", page_icon="📅", layout="wide")

init_routine_if_empty()

st.title("📅 주간 보기")

# --- 주의 시작 = 월요일 ---
def get_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())

if "week_start" not in st.session_state:
    st.session_state.week_start = get_monday(date.today())

def go_prev_week():
    st.session_state.week_start -= timedelta(days=7)

def go_next_week():
    st.session_state.week_start += timedelta(days=7)

def go_this_week():
    st.session_state.week_start = get_monday(date.today())

# --- 주 네비 ---
col_prev, col_label, col_next, col_today = st.columns([1, 4, 1, 1])
with col_prev:
    st.button("◀ 이전 주", on_click=go_prev_week, use_container_width=True)
with col_label:
    week_start = st.session_state.week_start
    week_end = week_start + timedelta(days=6)
    st.markdown(
        f"<h3 style='text-align: center; margin: 0;'>"
        f"{week_start.strftime('%Y. %m. %d')} ~ {week_end.strftime('%m. %d')}"
        f"</h3>",
        unsafe_allow_html=True
    )
with col_next:
    st.button("다음 주 ▶", on_click=go_next_week, use_container_width=True)
with col_today:
    st.button("이번 주", on_click=go_this_week, use_container_width=True)

st.write("---")

# --- 표 데이터 만들기 ---
week_start = st.session_state.week_start
days = [week_start + timedelta(days=i) for i in range(7)]
weekday_kr = ["월", "화", "수", "목", "금", "토", "일"]

# 컬럼 헤더 (예: "월\n04/29")
day_columns = [f"{weekday_kr[i]} {d.strftime('%m/%d')}" for i, d in enumerate(days)]

routine = get_routine()
range_data = load_range(week_start, week_start + timedelta(days=6))

# 그 주에 등장한 모든 항목 (루틴 + 그 주만의 추가 항목)
extra_items = []
for (d_str, item), _ in range_data.items():
    if item not in routine and item not in extra_items:
        extra_items.append(item)

all_items = routine + extra_items

# DataFrame 만들기
table_data = {}
for col_label, d in zip(day_columns, days):
    col_values = []
    for item in all_items:
        col_values.append(range_data.get((d.isoformat(), item), ""))
    table_data[col_label] = col_values

df = pd.DataFrame(table_data, index=all_items)

st.caption("💡 셀에 시간(예: `07:30`) 또는 `X` 직접 입력 가능. 빠른 입력은 일간 기록 페이지에서.")

# --- 편집 가능한 표 ---
edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="fixed",
    column_config={
        col: st.column_config.TextColumn(col, width="small")
        for col in day_columns
    },
    key="weekly_editor"
)

# --- 변경 감지해서 DB 저장 ---
if not edited_df.equals(df):
    changes = 0
    for item in all_items:
        for col_label, d in zip(day_columns, days):
            old_val = df.loc[item, col_label]
            new_val = edited_df.loc[item, col_label]
            if old_val != new_val:
                save_record(d, item, str(new_val) if new_val else "")
                changes += 1
    if changes > 0:
        st.success(f"{changes}개 셀 저장됨")
        st.rerun()

# --- 요약 ---
st.write("---")
with st.expander("📊 이 주 요약"):
    filled = sum(1 for item in all_items for col in day_columns if edited_df.loc[item, col])
    total = len(all_items) * 7
    st.write(f"채워진 칸: **{filled} / {total}** ({filled/total*100:.0f}%)")