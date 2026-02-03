import streamlit as st
import requests
import datetime

# ============================================
# 1️⃣ 페이지 기본 설정
# ============================================
st.set_page_config(
    page_title="네이버 뉴스 검색기",
    page_icon="📰",
    layout="centered"
)

# ============================================
# 2️⃣ 유틸리티 함수 (HTML 태그 제거 등)
# ============================================
def clean_title(title):
    """
    네이버 API 결과의 HTML 태그를 제거하고 특수문자를 변환합니다.
    """
    title = title.replace("<b>", "").replace("</b>", "")
    title = title.replace("&quot;", "\"").replace("&lt;", "<").replace("&gt;", ">")
    return title

# ============================================
# 3️⃣ 사이드바: API 키 설정
# ============================================
with st.sidebar:
    st.header("🔑 API 인증 정보")
    st.markdown("네이버 개발자 센터에서 발급받은 키를 입력하세요.")
    
    # 비밀번호 형태로 입력받아 보안 유지 (입력 시 별표 표시)
    client_id = st.text_input("Client ID", type="password")
    client_secret = st.text_input("Client Secret", type="password")
    
    st.info("💡 이 정보는 저장되지 않고 휘발됩니다.")
    st.markdown("---")
    st.markdown("[네이버 개발자 센터 바로가기](https://developers.naver.com)")

# ============================================
# 4️⃣ 메인 화면 UI
# ============================================
st.title("📰 네이버 뉴스 AI 검색기")
st.markdown("관심 있는 키워드를 입력하면 **실시간 최신 뉴스**를 찾아드립니다.")

# 검색어 입력
col1, col2 = st.columns([4, 1])
with col1:
    keyword = st.text_input("검색어를 입력하세요", placeholder="예: 인공지능, 삼성전자, 부동산")
with col2:
    # 줄맞춤을 위한 빈 공간
    st.write("") 
    st.write("")
    search_btn = st.button("검색 시작", type="primary")

# ============================================
# 5️⃣ 검색 로직 실행
# ============================================
if search_btn:
    # 1. 예외 처리: 키 입력 확인
    if not client_id or not client_secret:
        st.error("❌ 왼쪽 사이드바에 API ID와 Secret을 먼저 입력해주세요!")
        st.stop()
    
    # 2. 예외 처리: 검색어 확인
    if not keyword:
        st.warning("⚠️ 검색어를 입력해주세요.")
        st.stop()

    # 3. API 호출
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {
        "query": keyword,
        "display": 10,   # 10개 출력
        "sort": "sim"    # 정확도순
    }

    with st.spinner(f"🔍 '{keyword}' 관련 뉴스를 찾고 있습니다..."):
        try:
            response = requests.get(url, headers=headers, params=params)
            
            # 성공 (200)
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                if items:
                    st.success(f"총 {len(items)}개의 뉴스를 찾았습니다!")
                    st.markdown("---")
                    
                    for item in items:
                        # 데이터 추출
                        title = clean_title(item['title'])
                        link = item['originallink'] or item['link']
                        desc = clean_title(item['description'])
                        date = item['pubDate'][:16] # 날짜 포맷 간단히

                        # 카드 형태로 뉴스 출력
                        with st.expander(f"📢 {title}"):
                            st.markdown(f"**발행일:** {date}")
                            st.write(desc)
                            st.link_button("기사 원문 보기", link)
                else:
                    st.info("검색 결과가 없습니다.")
            
            # 에러 처리
            elif response.status_code == 401:
                st.error("❌ 인증 실패: Client ID와 Secret을 다시 확인해주세요.")
            elif response.status_code == 429:
                st.error("❌ 호출 한도 초과: 잠시 후 다시 시도해주세요.")
            else:
                st.error(f"❌ 오류 발생: {response.status_code}")

        except Exception as e:
            st.error(f"시스템 에러: {e}")