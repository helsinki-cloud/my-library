import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta

# --- 1. Supabase 접속 정보 설정 ---
SUPABASE_URL = "https://cqpdqbuspkndsbgdclnx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNxcGRxYnVzcGtuZHNiZ2RjbG54Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2Nzc5NTAsImV4cCI6MjA5MTI1Mzk1MH0.XuNFjhEoCSIQabPY8ND4tSW5zvu_N90IhEvaI9gPYH0"
ADMIN_PASSWORD = "00130"

# Supabase 클라이언트 초기화
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="도서관 통합 시스템", page_icon="📚", layout="wide")

# --- 2. CSS 스타일 (대식 님 맞춤형) ---
st.markdown("""
<style>
    div.stButton > button { font-size: 20px !important; height: 70px !important; width: 100% !important; font-weight: bold !important; border-radius: 12px !important; }
    .success-msg { font-size: 24px; font-weight: bold; color: #155724; background-color: #d4edda; padding: 25px; border-radius: 15px; text-align: center; border: 2px solid #c3e6cb; }
    .notice-box { font-size: 30px; font-weight: bold; color: #721c24; background-color: #f8d7da; padding: 30px; border-radius: 15px; text-align: center; margin-top: 40px; border: 3px solid #f5c6cb; }
    textarea, input { font-size: 18px !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. 데이터 조작 함수 ---
def fetch_all_books():
    res = supabase.table("library_db").select("*").execute()
    return pd.DataFrame(res.data)

def fetch_history():
    res = supabase.table("return_history").select("*").order("return_date", ascending=False).execute()
    return pd.DataFrame(res.data)

# 세션 모드 초기화
if 'mode' not in st.session_state:
    st.session_state.mode = 'main'

# --- 4. 화면 구성 ---
t1, t2 = st.tabs(["👋 대출/반납 이용하기", "🔐 관리자 모드"])

with t1:
    if st.session_state.mode == 'main':
        st.write("### 원하시는 작업을 선택해 주세요.")
        c1, c2 = st.columns(2)
        if c1.button("📘 대출하기 (Loan)"):
            st.session_state.mode = 'loan'; st.rerun()
        if c2.button("📗 반납하기 (Return)"):
            st.session_state.mode = 'return'; st.rerun()
        st.markdown('<div class="notice-box">📢 스터디룸 예약은 도서관 홈페이지에서 진행해주세요!</div>', unsafe_allow_html=True)

    # --- 대출 모드 ---
    elif st.session_state.mode == 'loan':
        if st.button("⬅ 처음으로 돌아가기"): st.session_state.mode = 'main'; st.rerun()
        borrower = st.text_input("대출자 학번 (교직원은 이름)")
        reg_text = st.text_area("도서 등록번호 스캔 (여러 권은 엔터로 구분)", height=200, 
                                placeholder="예:\n0025806\n0025807")

        if st.button("🚀 대출 실행 (Click)"):
            if not borrower or not reg_text.strip():
                st.warning("⚠️ 대출자 정보와 도서 번호를 모두 입력해야 합니다.")
            else:
                reg_list = [x.strip() for x in reg_text.split('\n') if x.strip()]
                loan_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
                
                for reg_no in reg_list:
                    # upsert: 있으면 수정, 없으면 새로 등록
                    data = {
                        "reg_no": reg_no,
                        "title": f"미등록도서({reg_no})",
                        "status": "대출중",
                        "borrower": borrower,
                        "loan_date": loan_date,
                        "due_date": due_date
                    }
                    supabase.table("library_db").upsert(data, on_conflict="reg_no").execute()
                
                st.markdown(f'<div class="success-msg">✅ 총 {len(reg_list)}권 대출 완료! (반납예정일: {due_date})</div>', unsafe_allow_html=True)
                if st.button("확인"): st.session_state.mode = 'main'; st.rerun()

    # --- 반납 모드 ---
    elif st.session_state.mode == 'return':
        if st.button("⬅ 처음으로 돌아가기"): st.session_state.mode = 'main'; st.rerun()
        reg_text = st.text_area("반납할 도서 번호 스캔 (여러 권은 엔터로 구분)", height=200)

        if st.button("✅ 반납 실행 (Click)"):
            if not reg_text.strip():
                st.warning("⚠️ 도서 번호를 입력해 주세요.")
            else:
                reg_list = [x.strip() for x in reg_text.split('\n') if x.strip()]
                return_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                for reg_no in reg_list:
                    # 기존 정보 조회
                    book_res = supabase.table("library_db").select("*").eq("reg_no", reg_no).execute()
                    if book_res.data:
                        book = book_res.data[0]
                        # 히스토리 기록
                        history_data = {
                            "reg_no": reg_no,
                            "title": book['title'],
                            "borrower": book['borrower'],
                            "return_date": return_date
                        }
                        supabase.table("return_history").insert(history_data).execute()
                        # 도서 상태 업데이트
                        supabase.table("library_db").update({"status": "대출가능", "borrower": "", "loan_date": "", "due_date": ""}).eq("reg_no", reg_no).execute()
                
                st.markdown(f'<div class="success-msg">🔙 총 {len(reg_list)}권 반납 처리가 완료되었습니다!</div>', unsafe_allow_html=True)
                if st.button("확인"): st.session_state.mode = 'main'; st.rerun()

# [탭 2: 관리자 모드]
with t2:
    st.header("🔐 도서관 관리자 전용")
    password = st.text_input("비밀번호", type="password")
    if password == ADMIN_PASSWORD:
        st.subheader("📊 1. 전체 도서 및 대출 현황")
        df_books = fetch_all_books()
        edited_books = st.data_editor(df_books, use_container_width=True, num_rows="dynamic", key="editor_books")
        
        if st.button("💾 도서 DB 변경사항 저장"):
            # 수동으로 행 삭제/수정 시 Supabase 반영 로직 필요 (여기선 조회 위주로 구성)
            st.info("개별 수정은 Supabase 대시보드에서 하거나, 추가 개발이 필요합니다.")

        st.divider()
        st.subheader("📜 2. 전체 반납 기록")
        df_history = fetch_history()
        st.dataframe(df_history, use_container_width=True)
        
        if st.button("🗑 전체 기록 삭제 (초기화)"):
            if st.checkbox("정말로 모든 반납 기록을 삭제하시겠습니까?"):
                supabase.table("return_history").delete().neq("reg_no", "0").execute()
                st.rerun()
