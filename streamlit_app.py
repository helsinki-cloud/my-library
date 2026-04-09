import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. 설정 및 경로 ---
DB_FILES = {
    "MAIN": "library_db.csv",
    "HISTORY": "return_history.csv"
}
ADMIN_PASSWORD = "00130"

st.set_page_config(page_title="도서관 시스템", page_icon="📚", layout="wide")

# --- 2. CSS 스타일 ---
st.markdown("""
<style>
    div.stButton > button { font-size: 20px !important; height: 60px !important; width: 100% !important; font-weight: bold !important; border-radius: 10px !important; }
    .success-msg { font-size: 24px; font-weight: bold; color: #155724; background-color: #d4edda; padding: 20px; border-radius: 10px; text-align: center; }
    .notice-box { font-size: 28px; font-weight: bold; color: #721c24; background-color: #f8d7da; padding: 25px; border-radius: 15px; text-align: center; margin-top: 30px; border: 2px solid #f5c6cb; }
    textarea { font-size: 18px !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. 데이터 엔진 ---
def initialize_system():
    if not os.path.exists(DB_FILES["MAIN"]):
        pd.DataFrame(columns=['등록번호', '자료명', '상태', '대출자', '대출일시', '반납일']).to_csv(DB_FILES["MAIN"], index=False, encoding='utf-8-sig')
    if not os.path.exists(DB_FILES["HISTORY"]):
        pd.DataFrame(columns=['반납일시', '반납자', '도서명', '등록번호']).to_csv(DB_FILES["HISTORY"], index=False, encoding='utf-8-sig')

initialize_system()

# 세션 상태에 데이터 로드
if 'df' not in st.session_state:
    st.session_state.df = pd.read_csv(DB_FILES["MAIN"], dtype=str).fillna('')
if 'history_df' not in st.session_state:
    st.session_state.history_df = pd.read_csv(DB_FILES["HISTORY"], dtype=str).fillna('')
if 'mode' not in st.session_state:
    st.session_state.mode = 'main'

def save_data():
    st.session_state.df.to_csv(DB_FILES["MAIN"], index=False, encoding='utf-8-sig')
    st.session_state.history_df.to_csv(DB_FILES["HISTORY"], index=False, encoding='utf-8-sig')

# --- 4. 메인 화면 ---
t1, t2 = st.tabs(["👋 대출/반납", "🔐 관리자 모드"])

with t1:
    if st.session_state.mode == 'main':
        c1, c2 = st.columns(2)
        if c1.button("📘 대출하기"):
            st.session_state.mode = 'loan'; st.rerun()
        if c2.button("📗 반납하기"):
            st.session_state.mode = 'return'; st.rerun()
        st.markdown('<div class="notice-box">📢 대출은 14일간 가능하며, 누구든 자유롭게 이용하세요!</div>', unsafe_allow_html=True)

    elif st.session_state.mode == 'loan':
        if st.button("⬅ 뒤로"): st.session_state.mode = 'main'; st.rerun()
        borrower = st.text_input("대출자 (이름 또는 학번)")
        reg_text = st.text_area("도서 등록번호 (여러 권은 엔터로 구분)", height=200)

        if st.button("대출 실행(Click)"):
            if not borrower or not reg_text.strip():
                st.warning("대출자와 도서 번호를 모두 입력해주세요.")
            else:
                reg_list = [x.strip() for x in reg_text.split('\n') if x.strip()]
                due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
                loan_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                for reg_no in reg_list:
                    idx = st.session_state.df[st.session_state.df['등록번호'] == reg_no].index
                    if not idx.empty:
                        st.session_state.df.at[idx[0], '상태'] = '대출중'
                        st.session_state.df.at[idx[0], '대출자'] = borrower
                        st.session_state.df.at[idx[0], '대출일시'] = loan_now
                        st.session_state.df.at[idx[0], '반납일'] = due_date
                    else:
                        new_book = {'등록번호': reg_no, '자료명': f'미등록도서({reg_no})', '상태': '대출중', '대출자': borrower, '대출일시': loan_now, '반납일': due_date}
                        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_book])], ignore_index=True)
                
                save_data()
                st.success(f"✅ 총 {len(reg_list)}권 대출 완료!")
                st.session_state.mode = 'main'; st.rerun()

    elif st.session_state.mode == 'return':
        if st.button("⬅ 뒤로"): st.session_state.mode = 'main'; st.rerun()
        reg_text = st.text_area("반납할 도서 번호 (여러 권은 엔터로 구분)", height=200)

        if st.button("반납 실행(Click)"):
            if not reg_text.strip():
                st.warning("도서 번호를 입력해주세요.")
            else:
                reg_list = [x.strip() for x in reg_text.split('\n') if x.strip()]
                return_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                for reg_no in reg_list:
                    idx = st.session_state.df[st.session_state.df['등록번호'] == reg_no].index
                    if not idx.empty:
                        # 히스토리에 기록 추가
                        history_entry = {
                            '반납일시': return_now,
                            '반납자': st.session_state.df.at[idx[0], '대출자'],
                            '도서명': st.session_state.df.at[idx[0], '자료명'],
                            '등록번호': reg_no
                        }
                        st.session_state.history_df = pd.concat([st.session_state.history_df, pd.DataFrame([history_entry])], ignore_index=True)
                        
                        # 도서 상태 변경
                        st.session_state.df.at[idx[0], '상태'] = '대출가능'
                        st.session_state.df.at[idx[0], '대출자'] = ''
                        st.session_state.df.at[idx[0], '대출일시'] = ''
                        st.session_state.df.at[idx[0], '반납일'] = ''
                
                save_data()
                st.success(f"🔙 총 {len(reg_list)}권 반납 완료!")
                st.session_state.mode = 'main'; st.rerun()

with t2:
    pw = st.text_input("관리자 비밀번호", type="password")
    if pw == ADMIN_PASSWORD:
        st.subheader("📋 1. 현재 대출 현황 (삭제/수정 가능)")
        # 대출 중인 도서만 필터링해서 보여주거나 전체 DB를 보여줄 수 있습니다. 
        # 여기서는 전체 도서 목록을 편집할 수 있게 했습니다.
        edited_df = st.data_editor(st.session_state.df, use_container_width=True, num_rows="dynamic", key="main_editor")
        if st.button("도서 DB 변경사항 저장"):
            st.session_state.df = edited_df
            save_data()
            st.success("도서 DB가 업데이트되었습니다.")

        st.divider()

        st.subheader("📜 2. 전체 반납 히스토리 (삭제/수정 가능)")
        # 최신 반납 기록이 위로 오도록 정렬해서 표시
        history_display = st.session_state.history_df.sort_index(ascending=False)
        edited_history = st.data_editor(history_display, use_container_width=True, num_rows="dynamic", key="history_editor")
        if st.button("반납 히스토리 변경사항 저장"):
            st.session_state.history_df = edited_history
            save_data()
            st.success("반납 히스토리가 업데이트되었습니다.")
