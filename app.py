import streamlit as st
import pandas as pd
import re
import os
import requests
import time
import google.generativeai as genai
from dotenv import load_dotenv

# --- 초기 설정: .env 파일에서 API 키 불러오기 ---
load_dotenv()
ALADIN_TTB_KEY = os.getenv('ALADIN_TTB_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- 데이터 로딩 및 키워드 필터링 함수 ---
@st.cache_data
def load_keywords_data(file_path):
    """
    최종 정리된 키워드 CSV 파일을 바로 불러옵니다.
    """
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        return df
    except FileNotFoundError:
        st.error(f"'{file_path}' 파일을 찾을 수 없습니다. app.py와 같은 위치에 있는지 확인해주세요.")
        return None
    except Exception as e:
        st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
        return None

def get_keywords_by_grade(df, grade, semester, subject):
    """
    정리된 데이터프레임에서 조건에 맞는 키워드를 필터링합니다.
    """
    try:
        condition = (df['학년'] == grade) & \
                    ((df['학기'] == semester) | (df['학기'] == '공통')) & \
                    (df['과목'] == subject)
        
        filtered_df = df[condition]
        if filtered_df.empty:
            return []
        
        return sorted(list(filtered_df['키워드'].unique()))
    except Exception as e:
        st.error(f"키워드 필터링 중 오류가 발생했습니다: {e}")
        return []


# --- API 연동 함수들 ---
def search_books_on_aladin(query):
    if not ALADIN_TTB_KEY: return "알라딘 TTBKey가 설정되지 않았습니다."
    URL = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
    params = {
        "ttbkey": ALADIN_TTB_KEY, "Query": query, "QueryType": "Keyword", 
        "MaxResults": 10, "start": 1, "SearchTarget": "Book",
        "output": "js", "Version": "20131101"
    }
    try:
        response = requests.get(URL, params=params, timeout=5)
        response.raise_for_status()
        return response.json().get("item", [])
    except requests.exceptions.RequestException: return []
    except Exception: return []

def get_similar_keyword(original_keyword, grade_info):
    if not GEMINI_API_KEY: return None
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"'{grade_info}' 수업의 '{original_keyword}'라는 키워드와 교육적으로 의미가 가장 유사한 도서 검색용 키워드 1개만 알려주세요. 다른 설명은 모두 생략하고 키워드 단어만 알려주세요."
        response = model.generate_content(prompt, safety_settings={'HARASSMENT':'block_none'})
        time.sleep(1)
        return response.text.strip()
    except Exception: return None

def generate_recommendation_from_candidates(grade_info, original_keyword, book_list):
    if not GEMINI_API_KEY: return "Gemini API 키가 설정되지 않았습니다."
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e: return f"Gemini 모델 초기화 중 오류: {e}"
    
    prompt = f"당신은 '{grade_info}' 수업 담당 교사에게 조언하는 교육 전문가입니다. '{original_keyword}' 주제와 관련하여 아래의 후보 도서 목록을 찾았습니다.\n\n[후보 도서 목록]\n"
    for book in book_list:
        prompt += f"- 제목: {book.get('title', '')}\n  저자: {book.get('author', '')}\n\n"
    prompt += "[요청 사항]\n1. 첫 줄에, 위 목록에서 '{grade_info}' 학생들에게 가장 추천하고 싶은 책 1~2권의 제목을 'RECOMMENDED_BOOKS: [책 제목 1], [책 제목 2]' 형식으로 작성해주세요.\n2. 다음 줄부터, '{original_keyword}' 주제의 교육적 중요성을 설명해주세요.\n3. 마지막으로, 당신이 선정한 책들을 왜 추천하는지, 그리고 수업과 어떻게 연계하면 좋을지에 대한 아이디어를 포함한 전문적인 추천사를 작성해주세요.\n\n[출력 형식]\n- 전문가적이고 신뢰감 있는 어조를 사용해주세요.\n- 추천하는 책의 제목은 반드시 '📖 **책 제목**' 형식으로 강조해서 표시해주세요."
    try:
        response = model.generate_content(prompt, safety_settings={'HARASSMENT':'block_none'})
        return response.text
    except Exception as e: return f"Gemini API 호출 중 오류: {e}"

# --- Streamlit UI 구성 ---
st.set_page_config(layout="wide")
st.title("교과서재(敎科書齋)")
st.write("AI 확장 검색으로 선생님의 수업과 독서를 연결해 드립니다.")

csv_file = '최종_정리된_키워드.csv'
df = load_keywords_data(csv_file)

if df is not None:
    st.header("1. 수업 정보를 선택해주세요.")
    col1, col2, col3 = st.columns(3)
    with col1:
        grade_options = sorted(df['학년'].unique())
        grade = st.selectbox("학년", options=grade_options)
    with col2:
        semester_options = sorted(df[df['학년'] == grade]['학기'].unique())
        semester = st.selectbox("학기", options=semester_options)
    with col3:
        subject_options = sorted(df[(df['학년'] == grade) & (df['학기'] == semester)]['과목'].unique())
        subject = st.selectbox("과목", options=subject_options)

    st.header("2. 교육과정 키워드를 선택해주세요.")
    keywords = get_keywords_by_grade(df, grade, semester, subject)
    
    if keywords:
        keyword_options = ["키워드를 선택하세요."] + keywords
        selected_keyword_option = st.selectbox("키워드 목록", options=keyword_options, label_visibility="collapsed")
    else:
        st.warning("해당 조건에 맞는 교육과정 키워드를 찾지 못했습니다.")

    st.header("3. 도서 추천 받기")
    default_keyword = selected_keyword_option if 'selected_keyword_option' in locals() and selected_keyword_option != "키워드를 선택하세요." else ""
    user_keyword_input = st.text_input("추천받고 싶은 키워드", value=default_keyword)

    if st.button("🤖 AI 도서 추천받기"):
        if user_keyword_input:
            st.divider()
            grade_info = f"{grade} {semester} {subject}"
            
            with st.status("AI 확장 검색 및 추천사 생성을 시작합니다...", expanded=True) as status:
                status.update(label="1/3: 교육적 유사 키워드를 생성하고 있습니다...")
                similar_keyword = get_similar_keyword(user_keyword_input, grade_info)
                
                search_keywords = [user_keyword_input]
                if similar_keyword:
                    st.write(f"- AI가 '**{similar_keyword}**' 키워드를 추가로 제안했습니다.")
                    search_keywords.append(similar_keyword)
                
                status.update(label="2/3: 원본 및 유사 키워드로 알라딘 도서를 통합 검색합니다...")
                candidate_books = []
                candidate_isbns = set()
                for kw in search_keywords:
                    st.write(f"- '**{kw}**'(으)로 도서를 검색합니다...")
                    books = search_books_on_aladin(kw)
                    for book in books:
                        if book.get('isbn13') and book['isbn13'] not in candidate_isbns:
                            candidate_books.append(book)
                            candidate_isbns.add(book['isbn13'])
                
                if not candidate_books:
                    status.update(label="검색 실패", state="error", expanded=True)
                    st.error(f"'{user_keyword_input}' 및 유사 키워드로 관련 도서를 찾지 못했습니다.")
                else:
                    st.write(f"✅ 총 {len(candidate_books)}권의 후보 도서를 찾았습니다.")
                    status.update(label="3/3: 후보 도서 중에서 최종 추천 도서를 선정하고 있습니다...")
                    recommendation_text = generate_recommendation_from_candidates(grade_info, user_keyword_input, candidate_books)
                    
                    lines = recommendation_text.split('\n')
                    recommended_titles = []
                    recommendation_body = recommendation_text
                    if lines and lines[0].startswith("RECOMMENDED_BOOKS:"):
                        titles_str = lines[0].replace("RECOMMENDED_BOOKS:", "").strip()
                        recommended_titles = [t.strip().strip('[]') for t in titles_str.split('], [')]
                        recommendation_body = "\n".join(lines[1:]).strip()

                    status.update(label="추천 완료!", state="complete", expanded=False)
                    
                    st.markdown("---")
                    st.markdown("### 📚 AI 최종 추천 도서")
                    
                    # ⭐️ 변경: AI 추천 제목과 실제 책 제목의 포함 관계를 확인하여 매칭률을 높임
                    recommended_books_data = []
                    if recommended_titles:
                        for rec_title in recommended_titles:
                            for book in candidate_books:
                                # AI 추천 제목이 실제 책 제목의 일부이거나, 그 반대인 경우를 모두 고려
                                if rec_title in book.get('title', '') or book.get('title', '') in rec_title:
                                    # 중복 추가 방지
                                    if book.get('isbn13') not in [b.get('isbn13') for b in recommended_books_data]:
                                        recommended_books_data.append(book)

                    if recommended_books_data:
                        for book in recommended_books_data:
                            col1, col2 = st.columns([1, 4])
                            with col1:
                                st.image(book.get('cover', ''))
                            with col2:
                                st.subheader(book.get('title', '제목 없음'))
                                st.text(f"저자: {book.get('author', '정보 없음')}")
                                st.text(f"가격: {book.get('priceSales', 0):,}원")
                                st.caption(f"요약: {book.get('description', '정보 없음')}")
                                st.markdown(f"[➡️ 알라딘에서 자세히 보기]({book.get('link', '#')})")
                            st.markdown("---")

                        st.markdown("### 💡 AI 교육 전문가 추천사")
                        st.markdown(recommendation_body)
                    else:
                        # AI가 추천한 책이 없거나, 검색 결과와 일치하지 않는 경우
                        st.error("AI가 추천한 도서를 실제 검색 결과에서 찾지 못했습니다. 다른 키워드로 다시 시도해보세요.")
                        st.markdown("---")
                        st.markdown("### 💡 AI 추천사 원문 (참고용)")
                        st.markdown(recommendation_body)
        else:
            st.error("키워드를 입력하거나 목록에서 선택해주세요!")
