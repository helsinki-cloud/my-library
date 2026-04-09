import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. 설정 및 경로 ---
# 파일 경로를 단순화하여 현재 폴더에 저장되도록 설정
DB_FILES = {
    "MAIN": "library_db.csv",
    "USER": "users_db.csv",
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
</style>
""", unsafe_allow_html=True)

# --- 3. 데이터 엔진 (초기화 및 로드) ---
def initialize_system():
    # 도서 DB 초기화 (샘플 도서 1권 포함)
    if not os.path.exists(DB_FILES["MAIN"]):
        df = pd.DataFrame(columns=['등록번호', '자료명', '상태', '대출자', '대출일시', '반납일'])
        df.loc[0] = ['1001', '파이썬 입문', '대출가능', '', '', '']
        df.to_csv(DB_FILES["MAIN"], index=False, encoding='utf-8-sig')
    
    # 이용자 DB 초기화 (샘플 학생 1명 포함 - 테스트용)
    if not os.path.exists(DB_FILES["USER"]):
        df = pd.DataFrame(columns=['학번', '이름'])
        df.loc[0] = ['2024001', '테스트학생']
        df.to_csv(DB_FILES["USER"], index=False, encoding='utf-8-sig')

    # 반납 히스토리 초기화
    if not os.path.exists(DB_FILES["HISTORY"]):
        pd.DataFrame(columns=['반납일시', '반납자', '도서명', '등록번호']).to_csv(DB_FILES["HISTORY"], index=False, encoding='utf-8-sig')

initialize_system()

# 데이터 불러오기
if 'df' not in st.session_state:
    st.session_state.df = pd.read_csv(DB_FILES["MAIN"], dtype=str).fillna('')
if 'users_df' not in st.session_state:
    st.session_state.users_df = pd.read_csv(DB_FILES["USER"], dtype=str).fillna('')
if 'mode' not in st.session_state:
    st.session_state.mode = 'main'

# --- 4. 메인 화면 ---
t1, t2, t3 = st.tabs(["👋 대출/반납", "📂 자료 관리", "🔐 관리자"])

with t1:
    if st.session_state.mode == 'main':
        c1, c2 = st.columns(2)
        if c1.button("📘 대출하기"):
            st.session_state.mode = 'loan'; st.rerun()
        if c2.button("📗 반납하기"):
            st.session_state.mode = 'return'; st.rerun()
        st.markdown('<div class="notice-box">📢 스터디룸 예약은 홈페이지를 이용해 주세요</div>', unsafe_allow_html=True)

    elif st.session_state.mode == 'loan':
        if st.button("⬅ 뒤로"): st.session_state.mode = 'main'; st.rerun()
        borrower = st.text_input("대출자 학번을 입력하세요")
        reg_no = st.text_input("도서 등록번호를 스캔하세요")

        if st.button("대출 실행"):
            if borrower in st.session_state.users_df['학번'].values:
                df = st.session_state.df
                idx = df[df['등록번호'] == reg_no].index
                if not idx.empty:
                    if df.at[idx[0], '상태'] == '대출가능':
                        df.at[idx[0], '상태'] = '대출중'
                        df.at[idx[0], '대출자'] = borrower
                        df.at[idx[0], '반납일'] = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
                        df.to_csv(DB_FILES["MAIN"], index=False, encoding='utf-8-sig')
                        st.success(f"✅ 대출 완료! 반납일: {df.at[idx[0], '반납일']}")
                        st.session_state.mode = 'main'
                    else: st.error("이미 대출 중인 도서입니다.")
                else: st.error("등록되지 않은 도서입니다.")
            else: st.error("등록되지 않은 이용자입니다.")

    elif st.session_state.mode == 'return':
        if st.button("⬅ 뒤로"): st.session_state.mode = 'main'; st.rerun()
        reg_no = st.text_input("반납할 도서 번호를 스캔하세요")
        if st.button("반납 실행"):
            df = st.session_state.df
            idx = df[df['등록번호'] == reg_no].index
            if not idx.empty:
                df.at[idx[0], '상태'] = '대출가능'
                df.at[idx[0], '대출자'] = ''
                df.to_csv(DB_FILES["MAIN"], index=False, encoding='utf-8-sig')
                st.success("🔙 반납 처리가 완료되었습니다.")
                st.session_state.mode = 'main'
            else: st.error("도서 정보를 찾을 수 없습니다.")

with t2:
    st.subheader("데이터 업로드")
    st.info("엑셀 파일(.xlsx)을 업로드하여 도서 목록이나 학생 명단을 갱신할 수 있습니다.")
    # (파일 업로드 기능은 기존과 동일하게 유지 가능)

with t3:
    pw = st.text_input("관리자 비밀번호", type="password")
    if pw == ADMIN_PASSWORD:
        st.write("현재 대출 현황")
        st.dataframe(st.session_state.df)
