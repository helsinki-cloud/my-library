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

# --- 2. CSS 스타일 (UI 디자인) ---
st.markdown("""
<style>
    div.stButton > button { font-size: 20px !important; height: 70px !important; width: 100% !important; font-weight: bold !important; border-radius: 12px !important; }
    .success-msg { font-size: 24px; font-weight: bold; color: #155724; background-color: #d4edda; padding: 25px; border-radius: 15px; text-align: center; border: 2px solid #c3e6cb; }
    .notice-box { font-size: 30px; font-weight: bold; color: #721c24; background-color: #f8d7da; padding: 30px; border-radius: 15px; text-align: center; margin-top: 40px; border: 3px solid #f5c6cb; }
    textarea, input { font-size: 18px !important; }
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
if 'history_df' not in st.session_state:
    st.session_state.history_df = pd.read_csv(DB_FILES["HISTORY"], dtype=str).fillna('')
if 'mode' not in st.session_state:
    st.session_state.mode = 'main'

def save_to_csv():
    st.session_state.df.to_csv(DB_FILES["MAIN"], index=False, encoding='utf-8-sig')
    st.session_state.history_df.to_csv(DB_FILES["HISTORY"], index=False, encoding='utf-8-sig')

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
            
        st.subheader("📘 대출 모드")
        # 요청사항 반영: 대출자 학번 (교직원은 이름)
        borrower = st.text_input("대출자 학번 (교직원은 이름)")
        
        # 요청사항 반영: 예시를 들어 설명
        reg_text = st.text_area("도서 등록번호 스캔 (여러 권은 엔터로 구분)", height=200, 
                                placeholder="바코드를 찍으면 번호가 입력됩니다. 여러 권일 경우 아래 예시처럼 줄을 바꿔서 찍어주세요.\n\n예시:\n0025806\n0025807\n0025808")

        if st.button("🚀 대출 실행 (Click)"):
            if not borrower or not reg_text.strip():
                st.warning("⚠️ 대출자 정보와 도서 번호를 모두 입력해야 합니다.")
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
                
                save_to_csv()
                st.markdown(f'<div class="success-msg">✅ {len(reg_list)}권 대출 완료!<br>반납 예정일: {due_date}</div>', unsafe_allow_html=True)
                if st.button("처음으로"): st.session_state.mode = 'main'; st.rerun()

    # --- 반납 모드 ---
    elif st.session_state.mode == 'return':
        if st.button("⬅ 처음으로 돌아가기"): st.session_state.mode = 'main'; st.rerun()

        st.subheader("📗 반납 모드")
        reg_text = st.text_area("도서 앞표지 등록번호 스캔 (여러 권은 엔터로 구분)", height=200,
                                placeholder="반납할 도서의 바코드를 스캔하세요.\n\n예시:\n0025806\n0025807")

        if st.button("✅ 반납 실행 (Click)"):
            if not reg_text.strip():
                st.warning("⚠️ 반납할 도서 번호를 입력해 주세요.")
            else:
                reg_list = [x.strip() for x in reg_text.split('\n') if x.strip()]
                return_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                for reg_no in reg_list:
                    idx = st.session_state.df[st.session_state.df['등록번호'] == reg_no].index
                    if not idx.empty:
                        history_entry = {'반납일시': return_now, '반납자': st.session_state.df.at[idx[0], '대출자'], '도서명': st.session_state.df.at[idx[0], '자료명'], '등록번호': reg_no}
                        st.session_state.history_df = pd.concat([st.session_state.history_df, pd.DataFrame([history_entry])], ignore_index=True)
                        st.session_state.df.at[idx[0], '상태'] = '대출가능'; st.session_state.df.at[idx[0], '대출자'] = ''; st.session_state.df.at[idx[0], '대출일시'] = ''; st.session_state.df.at[idx[0], '반납일'] = ''
                
                save_to_csv()
                st.markdown(f'<div class="success-msg">🔙 {len(reg_list)}권 반납 처리가 완료되었습니다!</div>', unsafe_allow_html=True)
                if st.button("처음으로"): st.session_state.mode = 'main'; st.rerun()

# [탭 2: 관리자 모드]
with t2:
    st.header("🔐 도서관 관리자 전용")
    password = st.text_input("비밀번호를 입력하세요", type="password")
    
    if password == ADMIN_PASSWORD:
        st.success("인증되었습니다.")
        
        st.subheader("📊 1. 전체 도서 및 대출 현황")
        edited_main = st.data_editor(st.session_state.df, use_container_width=True, num_rows="dynamic", key="main_db_editor")
        if st.button("💾 도서 DB 변경사항 저장"):
            st.session_state.df = edited_main
            save_to_csv(); st.toast("도서 DB가 저장되었습니다!")

        st.divider()

        st.subheader("📜 2. 전체 반납 기록 (히스토리)")
        history_display = st.session_state.history_df.sort_index(ascending=False)
        edited_history = st.data_editor(history_display, use_container_width=True, num_rows="dynamic", key="history_db_editor")
        if st.button("💾 반납 히스토리 변경사항 저장"):
            st.session_state.history_df = edited_history
            save_to_csv(); st.toast("반납 기록이 저장되었습니다!")
            
        st.divider()
        
        st.subheader("📥 데이터 백업")
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("도서 DB 다운로드 (.csv)", data=st.session_state.df.to_csv(index=False, encoding='utf-8-sig'), file_name=f"library_db_{datetime.now().strftime('%y%m%d')}.csv")
        with c2:
            st.download_button("반납 기록 다운로드 (.csv)", data=st.session_state.history_df.to_csv(index=False, encoding='utf-8-sig'), file_name=f"return_history_{datetime.now().strftime('%y%m%d')}.csv")
