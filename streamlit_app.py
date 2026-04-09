import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta

# --- 1. Supabase 접속 정보 ---
# 보안을 위해 나중에 st.secrets 방식으로 바꾸는 것이 좋습니다.
SUPABASE_URL = "https://cqpdqbuspkndsbgdclnx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNxcGRxYnVzcGtuZHNiZ2RjbG54Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2Nzc5NTAsImV4cCI6MjA5MTI1Mzk1MH0.XuNFjhEoCSIQabPY8ND4tSW5zvu_N90IhEvaI9gPYH0"
ADMIN_PASSWORD = "00130"

# Supabase 클라이언트 초기화
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 페이지 설정
st.set_page_config(page_title="간편 도서관 시스템", page_icon="📚", layout="wide")

# --- 2. CSS 스타일 설정 ---
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
    """현재 도서 DB 가져오기"""
    try:
        res = supabase.table("library_db").select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['reg_no', 'title', 'status', 'borrower', 'loan_date', 'due_date'])
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

def fetch_history():
    """반납 히스토리 가져오기 (오류 수정 완료)"""
    try:
        # desc=True 옵션으로 최신순 정렬
        res = supabase.table("return_history").select("*").order("return_date", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['id', 'reg_no', 'title', 'borrower', 'return_date'])
    except Exception as e:
        st.error(f"히스토리 로드 오류: {e}")
        return pd.DataFrame()

# --- 4. 메인 화면 로직 ---
if 'mode' not in st.session_state:
    st.session_state.mode = 'main'

t1, t2 = st.tabs(["👋 대출/반납 이용", "🔐 관리자 모드"])

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
        if st.button("⬅ 처음으로"): st.session_state.mode = 'main'; st.rerun()
        st.subheader("📘 대출하기")
        borrower = st.text_input("대출자 학번 (교직원은 이름)")
        reg_text = st.text_area("도서 등록번호 스캔 (여러 권은 엔터로 구분)", height=200, 
                                placeholder="예시:\n0025806\n0025807")

        if st.button("🚀 대출 실행 (Click)"):
            if not borrower or not reg_text.strip():
                st.warning("⚠️ 정보를 모두 입력해주세요.")
            else:
                reg_list = [x.strip() for x in reg_text.split('\n') if x.strip()]
                loan_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
                
                success_count = 0
                for r in reg_list:
                    data = {
                        "reg_no": r, "title": f"미등록도서({r})", "status": "대출중",
                        "borrower": borrower, "loan_date": loan_now, "due_date": due_date
                    }
                    try:
                        supabase.table("library_db").upsert(data, on_conflict="reg_no").execute()
                        success_count += 1
                    except Exception as e:
                        st.error(f"'{r}' 저장 실패: {e}")
                
                if success_count > 0:
                    st.markdown(f'<div class="success-msg">✅ {success_count}권 대출 완료!<br>반납 예정일: {due_date}</div>', unsafe_allow_html=True)
                    if st.button("홈으로 이동"): st.session_state.mode = 'main'; st.rerun()

    # --- 반납 모드 ---
    elif st.session_state.mode == 'return':
        if st.button("⬅ 처음으로"): st.session_state.mode = 'main'; st.rerun()
        st.subheader("📗 반납하기")
        reg_text = st.text_area("반납할 도서 바코드 스캔", height=200, placeholder="예시:\n0025806")

        if st.button("✅ 반납 실행 (Click)"):
            if not reg_text.strip():
                st.warning("⚠️ 바코드를 스캔해주세요.")
            else:
                reg_list = [x.strip() for x in reg_text.split('\n') if x.strip()]
                return_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                for r in reg_list:
                    # 1. 도서 정보 가져오기
                    res = supabase.table("library_db").select("*").eq("reg_no", r).execute()
                    if res.data:
                        book = res.data[0]
                        # 2. 히스토리에 추가
                        supabase.table("return_history").insert({
                            "reg_no": r, "title": book['title'], 
                            "borrower": book['borrower'], "return_date": return_now
                        }).execute()
                        # 3. 메인 DB 업데이트
                        supabase.table("library_db").update({
                            "status": "대출가능", "borrower": "", "loan_date": "", "due_date": ""
                        }).eq("reg_no", r).execute()
                
                st.markdown(f'<div class="success-msg">🔙 {len(reg_list)}권 반납 완료되었습니다!</div>', unsafe_allow_html=True)
                if st.button("홈으로 이동"): st.session_state.mode = 'main'; st.rerun()

# --- 5. 관리자 모드 ---
with t2:
    st.header("🔐 관리자 시스템")
    pw = st.text_input("관리자 비밀번호", type="password")
    if pw == ADMIN_PASSWORD:
        st.success("로그인 성공")
        
        tab_a, tab_b = st.tabs(["📊 대출 현황", "📜 반납 히스토리"])
        
        with tab_a:
            st.subheader("현재 대출 중인 도서 목록")
            df_main = fetch_all_books()
            # 대출중인 것만 필터링하거나 전체를 편집기로 보여줌
            edited_df = st.data_editor(df_main, use_container_width=True, num_rows="dynamic")
            if st.button("도서 DB 강제 저장"):
                # 실제론 개별 삭제 로직이 복잡하므로 여기선 조회 용도로 우선 권장
                st.info("수정/삭제는 Supabase 대시보드에서 하시는 것이 가장 확실합니다.")
        
        with tab_b:
            st.subheader("전체 반납 기록")
            df_hist = fetch_history()
            st.dataframe(df_hist, use_container_width=True)
            
            # CSV 다운로드 버튼
            csv = df_hist.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("반납 기록 백업 다운로드 (.csv)", csv, "return_history.csv")
