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

if 'df' not in st.session_state:
    st.session_state.df = pd.read_csv(DB_FILES["MAIN"], dtype=str).fillna('')
if 'mode' not in st.session_state:
    st.session_state.mode = 'main'

# --- 4. 메인 화면 ---
t1, t2 = st.tabs(["👋 대출/반납", "🔐 관리자 모드"])

with t1:
    if st.session_state.mode == 'main':
        c1, c2 = st.columns(2)
        if c1.button("📘 대출하기"):
            st.session_state.mode = 'loan'; st.rerun()
        if c2.button("📗 반납하기"):
            st.session_state.mode = 'return'; st.rerun()
        st.markdown('<div class="notice-box">📢 스터디룸 예약은 도서관 홈페이지에서 진행해주세요!</div>', unsafe_allow_html=True)

    elif st.session_state.mode == 'loan':
        if st.button("⬅ 뒤로"): st.session_state.mode = 'main'; st.rerun()
        borrower = st.text_input("대출자 학번 (교직원은 이름)")
        reg_text = st.text_area("도서 등록번호 (여러 권은 엔터로 구분)", height=200, placeholder="예:\n0025806\n0025807\n0025808")

        if st.button("대출 실행(Click)"):
            if not borrower or not reg_text.strip():
                st.warning("대출자와 도서 번호를 모두 입력해주세요.")
            else:
                df = st.session_state.df
                reg_list = [x.strip() for x in reg_text.split('\n') if x.strip()]
                due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
                loan_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                for reg_no in reg_list:
                    idx = df[df['등록번호'] == reg_no].index
                    if not idx.empty:
                        df.at[idx[0], '상태'] = '대출중'
                        df.at[idx[0], '대출자'] = borrower
                        df.at[idx[0], '대출일시'] = loan_now
                        df.at[idx[0], '반납일'] = due_date
                    else:
                        # 신규 도서면 자동으로 DB에 추가하며 대출 처리
                        new_book = {'등록번호': reg_no, '자료명': f'미등록도서({reg_no})', '상태': '대출중', '대출자': borrower, '대출일시': loan_now, '반납일': due_date}
                        df = pd.concat([df, pd.DataFrame([new_book])], ignore_index=True)
                
                df.to_csv(DB_FILES["MAIN"], index=False, encoding='utf-8-sig')
                st.session_state.df = df
                st.success(f"✅ 총 {len(reg_list)}권 대출 완료! (반납예정일: {due_date})")
                st.session_state.mode = 'main'

    elif st.session_state.mode == 'return':
        if st.button("⬅ 뒤로"): st.session_state.mode = 'main'; st.rerun()
        reg_text = st.text_area("도서 앞 표지 등록번호 바코드 스캔 (여러 권은 엔터로 구분)", height=200)

        if st.button("반납 실행(Click)"):
            if not reg_text.strip():
                st.warning("도서 번호를 입력해주세요.")
            else:
                df = st.session_state.df
                reg_list = [x.strip() for x in reg_text.split('\n') if x.strip()]
                for reg_no in reg_list:
                    idx = df[df['등록번호'] == reg_no].index
                    if not idx.empty:
                        df.at[idx[0], '상태'] = '대출가능'
                        df.at[idx[0], '대출자'] = ''
                        df.at[idx[0], '대출일시'] = ''
                        df.at[idx[0], '반납일'] = ''
                
                df.to_csv(DB_FILES["MAIN"], index=False, encoding='utf-8-sig')
                st.session_state.df = df
                st.success(f"🔙 총 {len(reg_list)}권 반납 완료!")
                st.session_state.mode = 'main'

with t2:
    pw = st.text_input("관리자 비밀번호", type="password")
    if pw == ADMIN_PASSWORD:
        st.subheader("📊 현재 도서/대출 DB 현황")
        st.dataframe(st.session_state.df, use_container_width=True)
        if st.button("DB 강제 새로고침"):
            st.session_state.df = pd.read_csv(DB_FILES["MAIN"], dtype=str).fillna('')
            st.rerun()
