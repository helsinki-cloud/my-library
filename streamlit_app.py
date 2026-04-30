import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import pytz
import time

# --- 1. 설정 및 접속 정보 ---
SUPABASE_URL = "https://cqpdqbuspkndsbgdclnx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNxcGRxYnVzcGtuZHNiZ2RjbG54Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2Nzc5NTAsImV4cCI6MjA5MTI1Mzk1MH0.XuNFjhEoCSIQabPY8ND4tSW5zvu_N90IhEvaI9gPYH0"
ADMIN_PASSWORD = "00130"

KST = pytz.timezone('Asia/Seoul')

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

st.set_page_config(page_title="간편 도서관 시스템", page_icon="📚", layout="wide")

# --- 2. UI 스타일 ---
st.markdown("""
<style>
    div.stButton > button { font-size: 22px !important; height: 75px !important; font-weight: bold !important; border-radius: 15px !important; }
    .success-msg { font-size: 24px; font-weight: bold; color: #155724; background-color: #d4edda; padding: 25px; border-radius: 15px; text-align: center; border: 2px solid #c3e6cb; line-height: 1.6; }
    .notice-box { font-size: 28px; font-weight: bold; color: #721c24; background-color: #f8d7da; padding: 30px; border-radius: 15px; text-align: center; margin-top: 40px; border: 3px solid #f5c6cb; }
    .highlight { color: #d63384; font-size: 30px; text-decoration: underline; font-weight: 800; }
    input { font-size: 20px !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. 데이터 로드 함수 ---
def fetch_all_books():
    res = supabase.table("library_db").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['reg_no', 'title', 'status', 'borrower', 'loan_date', 'due_date'])

def fetch_history():
    res = supabase.table("return_history").select("*").order("return_date", desc=True).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['id', 'reg_no', 'title', 'borrower', 'return_date'])

# 세션 상태 초기화
if 'mode' not in st.session_state:
    st.session_state.mode = 'main'

# --- 4. 화면 구성 ---
t1, t2 = st.tabs(["👋 대출/반납 이용", "🔐 관리자 모드"])

with t1:
    if st.session_state.mode == 'main':
        st.markdown("<h1 style='text-align: center;'>📚 무인 대출반납 시스템</h1>", unsafe_allow_html=True)
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("📘 대출하기 (Loan)"):
            st.session_state.mode = 'loan'; st.rerun()
        if c2.button("📗 반납하기 (Return)"):
            st.session_state.mode = 'return'; st.rerun()
        st.markdown('<div class="notice-box">대출 기간은 14일입니다. <br> 📢 스터디룸 예약은 도서관 홈페이지에서 진행해주세요!</div>', unsafe_allow_html=True)

    # --- 대출 모드 (Loan) ---
    elif st.session_state.mode == 'loan':
        if st.button("⬅ 뒤로가기"): st.session_state.mode = 'main'; st.rerun()
        st.subheader("📘 도서 대출")
        
        # 수정된 입력 문구
        borrower = st.text_input("학번을 입력해주세요(교직원은 성명)")
        # 수정된 placeholder
        reg_text = st.text_area("도서 등록번호 스캔 (엔터로 구분)", height=200, placeholder="바코드를 스캔하세요 ex) 0026528")

        if st.button("🚀 대출 확인"):
            if not borrower or not reg_text.strip():
                st.warning("⚠️ 정보가 누락되었습니다. 학번과 바코드를 확인해주세요.")
            else:
                reg_list = [x.strip() for x in reg_text.split('\n') if x.strip()]
                now_kst = datetime.now(KST)
                loan_date_str = now_kst.strftime("%Y-%m-%d %H:%M")
                due_date_str = (now_kst + timedelta(days=14)).strftime("%Y-%m-%d")
                
                with st.spinner("데이터 기록 중..."):
                    for r in reg_list:
                        # 기존 도서 제목 유지를 위해 선조회
                        existing = supabase.table("library_db").select("title").eq("reg_no", r).execute()
                        
                        update_data = {
                            "reg_no": r,
                            "status": "대출중",
                            "borrower": borrower,
                            "loan_date": loan_date_str,
                            "due_date": due_date_str
                        }
                        
                        if not existing.data:
                            update_data["title"] = f"미등록도서({r})"
                        
                        supabase.table("library_db").upsert(update_data, on_conflict="reg_no").execute()

                # 반납 예정일 강조 출력
                st.balloons()
                st.markdown(f"""
                <div class="success-msg">
                    ✅ <b>{len(reg_list)}권</b> 대출 완료!<br>
                    📅 반납 예정일: <span class="highlight">{due_date_str}</span><br>
                    <small>잠시 후 자동으로 메인 화면으로 이동합니다.</small>
                </div>
                """, unsafe_allow_html=True)
                
                time.sleep(5)
                st.session_state.mode = 'main'
                st.rerun()

    # --- 반납 모드 (Return) ---
    elif st.session_state.mode == 'return':
        if st.button("⬅ 뒤로가기"): st.session_state.mode = 'main'; st.rerun()
        st.subheader("📗 도서 반납")
        reg_text = st.text_area("반납할 도서 바코드 스캔", height=200, placeholder="바코드를 스캔하세요...")

        if st.button("✅ 반납 확인"):
            if not reg_text.strip():
                st.warning("⚠️ 바코드를 스캔해주세요.")
            else:
                reg_list = [x.strip() for x in reg_text.split('\n') if x.strip()]
                return_now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
                
                for r in reg_list:
                    res = supabase.table("library_db").select("*").eq("reg_no", r).execute()
                    
                    book_title = res.data[0]['title'] if res.data else f"미등록({r})"
                    borrower_name = res.data[0]['borrower'] if res.data else "기록없음"
                    
                    supabase.table("return_history").insert({
                        "reg_no": r, "title": book_title, "borrower": borrower_name, "return_date": return_now
                    }).execute()
                    
                    if res.data:
                        supabase.table("library_db").update({
                            "status": "대출가능", "borrower": "", "loan_date": "", "due_date": ""
                        }).eq("reg_no", r).execute()
                
                st.markdown(f'<div class="success-msg">🔙 {len(reg_list)}권 반납 처리가 완료되었습니다.</div>', unsafe_allow_html=True)
                time.sleep(3)
                st.session_state.mode = 'main'
                st.rerun()

# --- 5. 관리자 모드 ---
with t2:
    pw = st.text_input("관리자 인증", type="password")
    if pw == ADMIN_PASSWORD:
        st.success("인증되었습니다.")
        m_tab1, m_tab2 = st.tabs(["📊 대출 현황", "📜 기록 조회"])
        
        with m_tab1:
            df_books = fetch_all_books()
            st.data_editor(df_books, use_container_width=True, num_rows="dynamic", key="lib_editor")
            
        with m_tab2:
            df_hist = fetch_history()
            st.dataframe(df_hist, use_container_width=True)
            csv = df_hist.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("📥 내역 다운로드 (CSV)", csv, "return_history.csv")
