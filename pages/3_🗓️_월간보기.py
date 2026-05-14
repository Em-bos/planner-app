import streamlit as st
import pandas as pd
from datetime import date, timedelta
from calendar import monthrange
from db_utils import (
    init_routine_if_empty, get_routine, load_range, save_record
)

st.set_page_config(page_title="월간 보기", page_icon="🗓️", layout="wide")

init_routine_if_empty()

st.title("🗓️ 월간 보기")

# --- 월 선택 상태 ---
today = date.today()
if "view_year" not in st.session_state:
    st.session_state.view_year = today.year
if "view_month" not in st.session_state:
    st.session_state.view_month = today.month

def go_prev_month():
    y, m = st.session_state.view_year, st.session_state.view_month
    if m == 1:
        st.session_state.view_year = y - 1
        st.session_state.view_month = 12
    else:
        st.session_state.view_month = m - 1

def go_next_month():
    y, m = st.session_state.view_year, st.session_state.view_month
    if m == 12:
        st.session_state.view_year = y + 1
        st.session_state.view_month = 1
    else:
        st.session_state.view_month = m + 1

def go_this_month():
    st.session_state.view_year = today.year
    st.session_state.view_month = today.month

# --- 월 네비 ---
col_prev, col_label, col_next, col_today = st.columns([1, 4, 1, 1])
with col_prev:
    st.button("◀ 이전 달", on_click=go_prev_month, use_container_width=True)
with col_label:
    st.markdown(
        f"<h3 style='text-align: center; margin: 0;'>"
        f"{st.session_state.view_year}년 {st.session_state.view_month}월"
        f"</h3>",
        unsafe_allow_html=True
    )
with col_next:
    st.button("다음 달 ▶", on_click=go_next_month, use_container_width=True)
with col_today:
    st.button("이번 달", on_click=go_this_month, use_container_width=True)

st.write("---")

# --- 데이터 로딩 ---
year = st.session_state.view_year
month = st.session_state.view_month

# 그 달의 첫날, 마지막날
first_day = date(year, month, 1)
last_day = date(year, month, monthrange(year, month)[1])

# 달력 격자에 빈칸이 필요하니까 그 주의 월요일부터 끝주 일요일까지 다 가져옴
grid_start = first_day - timedelta(days=first_day.weekday())
grid_end = last_day + timedelta(days=(6 - last_day.weekday()))

range_data = load_range(grid_start, grid_end)
routine = get_routine()

# 그달에 등장한 추가 항목들 (그달 범위만)
month_data_items = set()
for (d_str, item), val in range_data.items():
    d_obj = date.fromisoformat(d_str)
    if first_day <= d_obj <= last_day:  
        month_data_items.add(item)

extra_items = [it for it in month_data_items if it not in routine]
all_items = routine + extra_items

# --- 1) 달력 모양 (HTML 테이블) ---
st.subheader("📆 달력")

weekday_kr = ["월", "화", "수", "목", "금", "토", "일"]

# CSS
st.markdown("""
<style>
.cal-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 3px;
    table-layout: fixed;
}
.cal-table th {
    text-align: center;
    font-weight: bold;
    padding: 6px 0;
    font-size: 13px;
}
.cal-table td {
    vertical-align: top;
    border-radius: 6px;
    padding: 6px;
    height: 75px;
    font-size: 12px;
    line-height: 1.3;
    width: 14.28%;
    overflow: hidden;
}
.cal-day-num {
    font-weight: bold;
    font-size: 14px;
    display: block;
}
.cal-summary {
    margin-top: 3px;
    font-size: 11px;
}
/* 모바일: 600px 이하 */
@media (max-width: 600px) {
    .cal-table {
        border-spacing: 1px;
    }
    .cal-table th {
        font-size: 10px;
        padding: 3px 0;
    }
    .cal-table td {
        padding: 2px;
        height: 55px;
        font-size: 9px;
        line-height: 1.15;
    }
    .cal-day-num {
        font-size: 11px;
    }
    .cal-summary {
        font-size: 8px;
        margin-top: 1px;
    }
}
/* 아주 좁은 화면: 폴드 접힘 */
@media (max-width: 420px) {
    .cal-table th {
        font-size: 9px;
    }
    .cal-table td {
        height: 50px;
        font-size: 8px;
    }
    .cal-day-num {
        font-size: 10px;
    }
}
</style>
""", unsafe_allow_html=True)

# HTML 만들기
html = ["<table class='cal-table'>"]

# 헤더
html.append("<thead><tr>")
for i, wk in enumerate(weekday_kr):
    color = "#ff4d4d" if i == 6 else ("#4d8bff" if i == 5 else "#ddd")
    html.append(f"<th style='color:{color};'>{wk}</th>")
html.append("</tr></thead>")

# 본문
html.append("<tbody>")
cur = grid_start
while cur <= grid_end:
    html.append("<tr>")
    for i in range(7):
        d = cur + timedelta(days=i)
        in_month = (d.month == month)
        is_today = (d == today)
        
        day_records = {item: range_data.get((d.isoformat(), item), "")
                       for item in all_items}
        filled = [v for v in day_records.values() if v]
        wake = day_records.get("기상", "")
        count = len(filled)
        
        if wake and wake != "X":
            summary = f"기상 {wake}<br>📝 {count}개"
        elif count > 0:
            summary = f"📝 {count}개"
        else:
            summary = "&nbsp;"
        
        if not in_month:
            bg = "#1a1a1a"
            text_color = "#555"
            border = "1px solid #222"
        elif is_today:
            bg = "#2a3f5f"
            text_color = "#fff"
            border = "2px solid #4d8bff"
        else:
            bg = "#262626"
            text_color = "#ddd"
            border = "1px solid #333"
        
        weekday = d.weekday()
        if weekday == 6:
            date_color = "#ff7777"
        elif weekday == 5:
            date_color = "#77aaff"
        else:
            date_color = text_color
        
        html.append(
            f"<td style='background:{bg}; border:{border}; color:{text_color};'>"
            f"<span class='cal-day-num' style='color:{date_color};'>{d.day}</span>"
            f"<div class='cal-summary'>{summary}</div>"
            f"</td>"
        )
    html.append("</tr>")
    cur += timedelta(days=7)
html.append("</tbody></table>")

st.markdown("".join(html), unsafe_allow_html=True)

st.write("")

# --- 2) 큰 표 ---
st.subheader("📋 전체 표")
st.caption("💡 셀 직접 편집 가능 (시간 또는 X)")

# 컬럼: 그달의 모든 날
month_days = []
d = first_day
while d <= last_day:
    month_days.append(d)
    d += timedelta(days=1)

day_columns = [f"{d.day}일({weekday_kr[d.weekday()]})" for d in month_days]

# 데이터프레임 만들기
table_data = {}
for col_label, d in zip(day_columns, month_days):
    col_values = []
    for item in all_items:
        col_values.append(range_data.get((d.isoformat(), item), ""))
    table_data[col_label] = col_values

df = pd.DataFrame(table_data, index=all_items)

edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="fixed",
    column_config={
        col: st.column_config.TextColumn(col, width="small")
        for col in day_columns
    },
    key=f"monthly_editor_{year}_{month}"
)

# 변경 감지 후 저장
if not edited_df.equals(df):
    changes = 0
    for item in all_items:
        for col_label, d in zip(day_columns, month_days):
            old_val = df.loc[item, col_label]
            new_val = edited_df.loc[item, col_label]
            if old_val != new_val:
                save_record(d, item, str(new_val) if new_val else "")
                changes += 1
    if changes > 0:
        st.success(f"{changes}개 셀 저장됨")
        st.rerun()

# --- 3) 월간 요약 ---
st.write("---")
st.subheader("📊 이 달 요약")

total_cells = len(all_items) * len(month_days)
filled_cells = sum(
    1 for item in all_items for d in month_days
    if range_data.get((d.isoformat(), item), "")
)

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("총 기록 수", f"{filled_cells} / {total_cells}",
              f"{filled_cells/total_cells*100:.0f}%")
with col_b:
    days_with_data = len(set(
        d for d in month_days for item in all_items
        if range_data.get((d.isoformat(), item), "")
    ))
    st.metric("기록한 날짜", f"{days_with_data} / {len(month_days)}일")
with col_c:
    # 항목별 X 횟수 (스킵 횟수)
    skipped = sum(
        1 for item in all_items for d in month_days
        if range_data.get((d.isoformat(), item), "") == "X"
    )
    st.metric("X (스킵) 표시", f"{skipped}회")

# 항목별 통계
with st.expander("📈 항목별 통계"):
    stats_rows = []
    for item in all_items:
        values = [range_data.get((d.isoformat(), item), "") for d in month_days]
        recorded = sum(1 for v in values if v and v != "X")
        skipped_count = sum(1 for v in values if v == "X")
        stats_rows.append({
            "항목": item,
            "기록": recorded,
            "X": skipped_count,
            "공란": len(month_days) - recorded - skipped_count,
        })
    if stats_rows:
        st.dataframe(pd.DataFrame(stats_rows), use_container_width=True, hide_index=True)
        