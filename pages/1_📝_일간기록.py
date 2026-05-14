import streamlit as st
from datetime import datetime, date, timedelta
from db_utils import (
    init_routine_if_empty, get_routine, add_routine_item,
    remove_routine_item, move_routine_item,
    load_day, save_record, delete_record, load_all
)

st.set_page_config(page_title="일간 기록", page_icon="📝", layout="wide")

init_routine_if_empty()

st.title("📝 일간 기록")

if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today()

# --- 콜백 ---
def go_prev_day():
    st.session_state.selected_date -= timedelta(days=1)

def go_next_day():
    st.session_state.selected_date += timedelta(days=1)

def go_today():
    st.session_state.selected_date = date.today()

def add_extra_item(name):
    d = st.session_state.selected_date
    save_record(d, name, "")
    st.session_state[f"time_{d}_{name}"] = ""

def set_now(name):
    d = st.session_state.selected_date
    now = datetime.now().strftime("%H:%M")
    save_record(d, name, now)
    st.session_state[f"time_{d}_{name}"] = now

def set_x(name):
    d = st.session_state.selected_date
    save_record(d, name, "X")
    st.session_state[f"time_{d}_{name}"] = "X"

def save_text_input(name):
    d = st.session_state.selected_date
    value = st.session_state[f"time_{d}_{name}"]
    save_record(d, name, value)

def remove_extra_item(name):
    d = st.session_state.selected_date
    delete_record(d, name)

# --- 사이드바 ---
with st.sidebar:
    st.header("⚙️ 고정 루틴 관리")
    st.caption("매일 자동으로 표시되는 항목들")
    
    routine = get_routine()
    for i, name in enumerate(routine):
        c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
        with c1:
            st.write(f"{i+1}. {name}")
        with c2:
            if i > 0:
                st.button("⬆", key=f"up_{name}", on_click=move_routine_item, args=(name, -1))
        with c3:
            if i < len(routine) - 1:
                st.button("⬇", key=f"down_{name}", on_click=move_routine_item, args=(name, +1))
        with c4:
            st.button("✕", key=f"rm_{name}", on_click=remove_routine_item, args=(name,))
    
    st.write("---")
    new_routine = st.text_input("새 루틴 항목", key="new_routine_input")
    if st.button("루틴에 추가", use_container_width=True):
        if new_routine:
            if add_routine_item(new_routine):
                st.success(f"'{new_routine}' 루틴 추가됨")
            else:
                st.warning("이미 있는 항목이야")

# --- 날짜 네비 ---
col_prev, col_date, col_next, col_today = st.columns([1, 4, 1, 1])
with col_prev:
    st.button("◀", on_click=go_prev_day, use_container_width=True)
with col_date:
    selected = st.session_state.selected_date
    weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][selected.weekday()]
    is_today = " (오늘)" if selected == date.today() else ""
    st.markdown(
        f"<h3 style='text-align: center; margin: 0;'>"
        f"{selected.strftime('%Y년 %m월 %d일')} ({weekday_kr}){is_today}"
        f"</h3>",
        unsafe_allow_html=True
    )
with col_next:
    st.button("▶", on_click=go_next_day, use_container_width=True)
with col_today:
    st.button("오늘", on_click=go_today, use_container_width=True)

st.write("---")

# --- 기록 ---
d = st.session_state.selected_date
day_data = load_day(d)
routine = get_routine()
extra_items = [name for name in day_data.keys() if name not in routine]
items_to_show = routine + extra_items

def render_row(item_name, is_routine):
    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
    with col1:
        if is_routine:
            st.write(f"**{item_name}**")
        else:
            st.write(f"*{item_name}* 🆕")
    with col2:
        widget_key = f"time_{d}_{item_name}"
        if widget_key not in st.session_state:
            st.session_state[widget_key] = day_data.get(item_name, "")
        st.text_input("시간", key=widget_key, label_visibility="collapsed",
                      on_change=save_text_input, args=(item_name,))
    with col3:
        st.button("지금", key=f"now_{d}_{item_name}",
                  on_click=set_now, args=(item_name,))
    with col4:
        st.button("X", key=f"x_{d}_{item_name}",
                  on_click=set_x, args=(item_name,))
    with col5:
        if not is_routine:
            st.button("🗑️", key=f"del_{d}_{item_name}",
                      on_click=remove_extra_item, args=(item_name,))

st.subheader("📝 기록")
for item in items_to_show:
    render_row(item, is_routine=(item in routine))

st.write("---")
st.caption("💡 이 날만 따로 추가할 항목 (예: 회의, 병원)")
extra = st.text_input("추가 항목", key="extra_input", label_visibility="collapsed")
if st.button("이 날에만 추가"):
    if not extra:
        st.warning("이름을 적어줘")
    elif extra in items_to_show:
        st.warning("이미 있어")
    else:
        add_extra_item(extra)
        st.success(f"'{extra}' 추가됨 (오늘만)")

st.write("---")
with st.expander("📊 전체 데이터 보기"):
    all_records = load_all()
    if not all_records:
        st.write("아직 데이터 없음")
    else:
        st.write(f"총 {len(all_records)}개 레코드")
        st.dataframe(
            {"날짜": [r[0] for r in all_records],
             "항목": [r[1] for r in all_records],
             "값": [r[2] for r in all_records]},
            use_container_width=True, hide_index=True
        )