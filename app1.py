import streamlit as st
import requests
import yfinance as yf
import pandas as pd

# ============================================
# 1️⃣ 페이지 기본 설정
# ============================================
st.set_page_config(
    page_title="경제 뉴스 & 원화 시세 대시보드",
    page_icon="🇰🇷",
    layout="centered"
)

# ============================================
# 2️⃣ 데이터 처리 함수 (환율 적용)
# ============================================
def get_market_data():
    """
    금(GC=F), 은(SI=F), 원달러 환율(KRW=X) 데이터를 가져와
    원화 기준 가격을 계산합니다.
    """
    try:
        # 1. 데이터 가져오기 (금, 은, 환율)
        tickers = ['GC=F', 'SI=F', 'KRW=X']
        # period='1d': 하루치 데이터, interval='1m': 1분 간격
        data = yf.download(tickers, period='1d', interval='1m', progress=False)
        
        if data.empty:
            return None

        # 2. 최신 데이터(마지막 행)와 시초가(첫 행) 추출
        last_row = data.iloc[-1]
        prev_row = data.iloc[0]

        # 3. 각 지표별 현재가 추출 (MultiIndex 처리)
        # yfinance 버전에 따라 접근 방식이 다를 수 있어 안전하게 처리
        try:
            rate_now = last_row['Close']['KRW=X']
            gold_usd = last_row['Close']['GC=F']
            silver_usd = last_row['Close']['SI=F']
            
            rate_open = prev_row['Open']['KRW=X']
            gold_open = prev_row['Open']['GC=F']
            silver_open = prev_row['Open']['SI=F']
        except KeyError:
            # 컬럼 구조가 다를 경우를 대비한 예외 처리
            return None

        # 4. 원화 환산 (현재가)
        gold_krw = gold_usd * rate_now
        silver_krw = silver_usd * rate_now

        # 5. 원화 환산 (시초가 - 변동폭 계산용)
        gold_krw_open = gold_open * rate_open
        silver_krw_open = silver_open * rate_open

        return {
            "rate_now": rate_now,
            "rate_delta": rate_now - rate_open,
            "gold_krw": gold_krw,
            "gold_delta": gold_krw - gold_krw_open,
            "silver_krw": silver_krw,
            "silver_delta": silver_krw - silver_krw_open,
            "gold_usd": gold_usd # 참고용 달러 가격
        }

    except Exception as e:
        return None

def clean_title(title):
    """HTML 태그 제거 및 특수문자 처리"""
    title = title.replace("<b>", "").replace("</b>", "")
    title = title.replace("&quot;", "\"").replace("&lt;", "<").replace("&gt;", ">")
    return title

# ============================================
# 3️⃣ 사이드바: API 설정
# ============================================
with st.sidebar:
    st.header("⚙️ 설정")
    st.markdown("뉴스 검색을 위해 네이버 API 키가 필요합니다.")
    
    # API 키 입력 (비밀번호 모드)
    client_id = st.text_input("Client ID", type="password")
    client_secret = st.text_input("Client Secret", type="password")
    
    st.markdown("---")
    st.caption("Developed with Streamlit & Naver API")

# ============================================
# 4️⃣ 메인 화면: 시장 지표 (Dashboard)
# ============================================
st.title("🇰🇷 오늘의 시장 & 뉴스")
st.markdown("실시간 **환율**과 환산된 **원화(KRW) 원자재 가격**입니다.")

# 데이터 로딩 애니메이션
with st.spinner('시장 데이터를 분석 중입니다...'):
    market_data = get_market_data()

st.subheader("💰 실시간 시세 (KRW 기준)")

# 3개의 컬럼 생성
col1, col2, col3 = st.columns(3)

if market_data:
    # 1. 환율 정보
    with col1:
        st.metric(
            label="🇺🇸 원/달러 환율",
            value=f"{market_data['rate_now']:,.2f} 원",
            delta=f"{market_data['rate_delta']:.2f} 원"
        )
    
    # 2. 금 정보
    with col2:
        st.metric(
            label="🥇 금 (1온스)",
            value=f"{market_data['gold_krw']:,.0f} 원",
            delta=f"{market_data['gold_delta']:.0f} 원"
        )
        st.caption(f"국제시세: ${market_data['gold_usd']:.2f}")

    # 3. 은 정보
    with col3:
        st.metric(
            label="🥈 은 (1온스)",
            value=f"{market_data['silver_krw']:,.0f} 원",
            delta=f"{market_data['silver_delta']:.0f} 원"
        )
    
    st.markdown("---")
    st.info("💡 위 가격은 국제 선물 시세($)에 실시간 환율을 곱한 **단순 환산 가격**입니다. (국내 소매가와 다름)")
    
else:
    st.error("📉 시장 데이터를 불러오는데 실패했습니다. (잠시 후 다시 시도해주세요)")

st.markdown("---")

# ============================================
# 5️⃣ 메인 화면: 뉴스 검색
# ============================================
st.subheader("📰 관련 뉴스 검색")

search_col, btn_col = st.columns([4, 1])
with search_col:
    keyword = st.text_input("검색어", placeholder="예: 금값 전망, 환율 예측, 경제 위기")
with btn_col:
    st.write("") # 줄맞춤용 공백
    st.write("")
    search_btn = st.button("검색", type="primary")

if search_btn:
    # 1. 예외 처리
    if not client_id or not client_secret:
        st.error("🔒 왼쪽 사이드바에 Client ID와 Secret을 먼저 입력해주세요.")
        st.stop()
        
    if not keyword:
        st.warning("⚠️ 검색어를 입력해주세요.")
        st.stop()

    # 2. API 호출
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    params = {"query": keyword, "display": 5, "sort": "date"} # 최신순 정렬

    with st.spinner(f"'{keyword}' 관련 뉴스를 가져오는 중..."):
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                items = response.json().get("items", [])
                
                if items:
                    st.success(f"최신 뉴스 {len(items)}건을 찾았습니다.")
                    for item in items:
                        title = clean_title(item['title'])
                        link = item['originallink'] or item['link']
                        desc = clean_title(item['description'])
                        date = item['pubDate'][:16] # 날짜 포맷 자르기
                        
                        # 뉴스 카드 출력
                        with st.expander(f"{title}"):
                            st.caption(f"📅 {date}")
                            st.write(desc)
                            st.link_button("기사 원문 읽기", link)
                else:
                    st.info("검색 결과가 없습니다.")
            elif response.status_code == 401:
                st.error("❌ 인증 실패: Client ID와 Secret을 확인하세요.")
            elif response.status_code == 429:
                st.error("❌ 호출 한도 초과: 잠시 후 다시 시도하세요.")
            else:
                st.error(f"❌ API 오류: {response.status_code}")
                
        except Exception as e:
            st.error(f"❌ 접속 오류 발생: {e}")