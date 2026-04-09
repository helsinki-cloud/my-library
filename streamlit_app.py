import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import pytz # 시간대 설정을 위한 라이브러리

# --- 1. 접속 정보 및 설정 ---
SUPABASE_URL = "https://cqpdqbuspkndsbgdclnx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNxcGRxYnVzcGtuZHNiZ2RjbG54Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2Nzc5NTAsImV4cCI6MjA5MTI1Mzk1MH0.XuNFjhEoCSIQabPY8ND4tSW5zvu_N90IhEvaI9gPYH0"
ADMIN_PASSWORD = "00130"

# 한국 시간대 정의
KST = pytz.timezone('Asia/Seoul')

# Supabase 클라이언트 초기화
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="간편 도서 대출 시스템", page_icon="📚", layout="wide")

# --- 2. UI 디자인 ---
st.markdown("""
<style>
    div.stButton > button { font-size: 22px !important; height: 75px !important; font-weight: bold !important; border-radius: 15px !important; }
    .success-msg { font-size: 24px; font-weight: bold; color: #155724; background-color: #d4edda; padding: 25px; border-radius: 15px; text-align: center; border: 2px solid #c3e6cb; }
    .notice-box { font-size: 30px; font-weight: bold; color: #721c24; background-color: #f8d7da; padding: 30px; border-radius: 15px; text-align: center; margin-top: 40px; border: 3px solid #f5c6cb; }
    textarea, input { font-size: 18px !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. 데이터 로드 함수 ---
def fetch_all_books():
    try:
        res = supabase.table("library_db").select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['reg_no', 'title', 'status', 'borrower', 'loan_date', 'due_date'])
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

def fetch_history():
    try:
        # 최신순 정렬 (desc=True)
        res = supabase.table("return_history").select("*").order("return_date", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['id', 'reg_no', 'title', 'borrower', 'return_date'])
    except Exception as e:
        st.error(f"히스토리 로드 오류: {e}")
        return pd.DataFrame()

# 세션 상태 관리
if 'mode' not in st.session_state:
    st.session_state.mode = 'main'

# --- 4. 메인 화면 ---
t1, t2 = st.tabs(["👋 대출/반납", "🔐 관리자 모드"])

with t1:
    if st.session_state.mode == 'main':
        st.markdown("<h2 style='text-align: center;'>원하시는 버튼을 눌러주세요</h2>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("📘 대출하기 (Loan)"):
            st.session_state.mode = 'loan'; st.rerun()
        if c2.button("📗 반납하기 (Return)"):
            st.session_state.mode = 'return'; st.rerun()
        st.markdown('<div class="notice-box">📢 스터디룸 예약은 도서관 홈페이지에서 진행해주세요!</div>', unsafe_allow_html=True)

    # --- 대출 모드 ---
    elif st.session_state.mode == 'loan':
        if st.button("⬅ 뒤로가기"): st.session_state.mode = 'main'; st.rerun()
        borrower = st.text_input("대출자 학번 (교직원은 이름)")
        reg_text = st.text_area("도서 등록번호 스캔 (여러 권은 엔터로 구분)", height=200, placeholder="예:\n0025806\n0025807")

        if st.button("🚀 대출 실행 (Click)"):
            if not borrower or not reg_text.strip():
                st.warning("⚠️ 대출자 정보와 도서 번호를 입력해주세요.")
            else:
                reg_list = [x.strip() for x in reg_text.split('\n') if x.strip()]
                # [시간 설정] 서버 시간이 아닌 한국 시간으로 고정
                now_kst = datetime.now(KST)
                loan_now = now_kst.strftime("%Y-%m-%d %H:%M")
                due_date = (now_kst + timedelta(days=14)).strftime("%Y-%m-%d")
                
                for r in reg_list:
                    data = {
                        "reg_no": r, "title": f"미등록도서({r})", "status": "대출중",
                        "borrower": borrower, "loan_date": loan_now, "due_date": due_date
                    }
                    supabase.table("library_db").upsert(data, on_conflict="reg_no").execute()
                
                st.markdown(f'<div class="success-msg">✅ {len(reg_list)}권 대출 완료!<br>반납 예정일: {due_date}</div>', unsafe_allow_html=True)
                if st.button("홈으로"): st.session_state.mode = 'main'; st.rerun()

    # --- 반납 모드 ---
    elif st.session_state.mode == 'return':
        if st.button("⬅ 뒤로가기"): st.session_state.mode = 'main'; st.rerun()
        reg_text = st.text_area("반납할 도서 바코드 스캔", height=200)

        if st.button("✅ 반납 실행 (Click)"):
            if not reg_text.strip():
                st.warning("⚠️ 바코드를 스캔해주세요.")
            else:
                reg_list = [x.strip() for x in reg_text.split('\n') if x.strip()]
                # [시간 설정] 한국 시간으로 고정
                return_now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
                
                for r in reg_list:
                    res = supabase.table("library_db").select("*").eq("reg_no", r).execute()
                    if res.data:
                        book = res.data[0]
                        # 히스토리 저장
                        supabase.table("return_history").insert({
                            "reg_no": r, "title": book['title'], 
                            "borrower": book['borrower'], "return_date": return_now
                        }).execute()
                        # 대출 정보 초기화
                        supabase.table("library_db").update({
                            "status": "대출가능", "borrower": "", "loan_date": "", "due_date": ""
                        }).eq("reg_no", r).execute()
                
                st.markdown(f'<div class="success-msg">🔙 {len(reg_list)}권 반납 완료되었습니다!</div>', unsafe_allow_html=True)
                if st.button("홈으로"): st.session_state.mode = 'main'; st.rerun()

# --- 5. 관리자 모드 ---
with t2:
    pw = st.text_input("비밀번호", type="password")
    if pw == ADMIN_PASSWORD:
        st.success("인증 완료")
        m_tab1, m_tab2 = st.tabs(["📊 실시간 대출 현황", "📜 반납 기록 조회"])
        
        with m_tab1:
            st.subheader("📋 전체 도서 목록")
            df_books = fetch_all_books()
            st.data_editor(df_books, use_container_width=True, num_rows="dynamic")
            
        with m_tab2:
            st.subheader("📜 반납 히스토리 (최신순)")
            df_hist = fetch_history()
            st.dataframe(df_hist, use_container_width=True)
            # 백업용 다운로드 버튼
            csv = df_hist.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("엑셀 백업 다운로드", csv, "return_history.csv")
