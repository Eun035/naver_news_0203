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
# 2️⃣ 데이터 처리 함수 (안정성 강화)
# ============================================
def get_current_price(ticker_symbol):
    """
    특정 티커의 현재가와 전일 대비 변동액을 가져옵니다.
    데이터가 없을 경우 None을 반환합니다.
    """
    try:
        # Ticker 객체 생성
        ticker = yf.Ticker(ticker_symbol)
        
        # 1일치 데이터를 1분 간격으로 가져오기 (실시간에 가깝게)
        df = ticker.history(period="1d", interval="1m")
        
        # 장이 닫혀서 1분 데이터가 없으면, 최근 5일치 일별 데이터로 대체
        if df.empty:
            df = ticker.history(period="5d")
        
        if df.empty:
            return None, None

        # 가장 최근 데이터 (현재가)
        last_row = df.iloc[-1]
        current_price = last_row['Close']
        
        # 시초가 (장 시작 가격) - 변동폭 계산용
        open_price = df.iloc[0]['Open']
        
        # 변동액 계산
        delta = current_price - open_price
        
        return current_price, delta

    except Exception as e:
        # 에러 발생 시 콘솔에만 출력하고 None 반환
        print(f"Error fetching {ticker_symbol}: {e}")
        return None, None

def get_market_data():
    """
    금, 은, 환율 데이터를 각각 따로 가져와서 안전하게 계산합니다.
    """
    # 1. 환율 가져오기 (KRW=X)
    rate_now, rate_delta = get_current_price('KRW=X')
    
    # 2. 금값 가져오기 (GC=F)
    gold_usd, gold_delta_usd = get_current_price('GC=F')
    
    # 3. 은값 가져오기 (SI=F)
    silver_usd, silver_delta_usd = get_current_price('SI=F')

    # 데이터가 하나라도 없으면 None 반환
    if rate_now is None or gold_usd is None or silver_usd is None:
        return None

    # 4. 원화로 변환 (현재가)
    gold_krw = gold_usd * rate_now
    silver_krw = silver_usd * rate_now

    # 5. 원화로 변환 (변동폭)
    # 변동폭(원화) = (달러 변동폭 * 현재 환율) + (현재 달러가격 * 환율 변동폭) ...은 복잡하므로
    # 약식으로 '달러 변동폭 * 현재 환율'만 적용하여 근사치 제공
    gold_delta_krw = gold_delta_usd * rate_now
    silver_delta_krw = silver_delta_usd * rate_now

    return {
        "rate_now": rate_now,
        "rate_delta": rate_delta,
        "gold_krw": gold_krw,
        "gold_delta": gold_delta_krw,
        "silver_krw": silver_krw,
        "silver_delta": silver_delta_krw,
        "gold_usd": gold_usd,
        "silver_usd": silver_usd
    }

def clean_title(title):
    """HTML 태그 제거"""
    title = title.replace("<b>", "").replace("</b>", "")
    title = title.replace("&quot;", "\"").replace("&lt;", "<").replace("&gt;", ">")
    return title

# ============================================
# 3️⃣ 사이드바: API 설정
# ============================================
with st.sidebar:
    st.header("⚙️ 설정")
    client_id = st.text_input("Client ID", type="password")
    client_secret = st.text_input("Client Secret", type="password")
    st.info("API 키가 없으면 뉴스 검색이 작동하지 않습니다.")

# ============================================
# 4️⃣ 메인 화면: 시장 지표
# ============================================
st.title("🇰🇷 오늘의 시장 & 뉴스")
st.markdown("실시간 **환율**과 환산된 **원화(KRW) 원자재 가격**입니다.")

# 데이터 로딩
with st.spinner('시장 데이터를 분석 중입니다...'):
    market_data = get_market_data()

st.subheader("💰 실시간 시세 (KRW 기준)")

col1, col2, col3 = st.columns(3)

if market_data:
    # 1. 환율
    with col1:
        st.metric(
            label="🇺🇸 원/달러 환율",
            value=f"{market_data['rate_now']:,.2f} 원",
            delta=f"{market_data['rate_delta']:.2f} 원"
        )
    
    # 2. 금
    with col2:
        st.metric(
            label="🥇 금 (1온스)",
            value=f"{market_data['gold_krw']:,.0f} 원",
            delta=f"{market_data['gold_delta']:.0f} 원"
        )
        st.caption(f"국제시세: ${market_data['gold_usd']:.2f}")

    # 3. 은
    with col3:
        st.metric(
            label="🥈 은 (1온스)",
            value=f"{market_data['silver_krw']:,.0f} 원",
            delta=f"{market_data['silver_delta']:.0f} 원"
        )
        st.caption(f"국제시세: ${market_data['silver_usd']:.2f}")
    
    st.markdown("---")
    st.info("💡 위 가격은 국제 선물 시세($)에 실시간 환율을 곱한 **단순 환산 가격**입니다. (국내 소매가와 다름)")

else:
    # 데이터 불러오기 실패 시 대체 메시지
    st.warning("📉 현재 시장 데이터를 불러올 수 없습니다. (장이 닫혔거나 통신 오류일 수 있습니다)")
    st.markdown("---")


# ============================================
# 5️⃣ 메인 화면: 뉴스 검색
# ============================================
st.subheader("📰 관련 뉴스 검색")

search_col, btn_col = st.columns([4, 1])
with search_col:
    keyword = st.text_input("검색어", placeholder="예: 금값 전망, 환율 예측, 경제 위기")
with btn_col:
    st.write("") 
    st.write("")
    search_btn = st.button("검색", type="primary")

if search_btn:
    if not client_id or not client_secret:
        st.error("🔒 왼쪽 사이드바에 Client ID와 Secret을 먼저 입력해주세요.")
        st.stop()
        
    if not keyword:
        st.warning("⚠️ 검색어를 입력해주세요.")
        st.stop()

    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    params = {"query": keyword, "display": 5, "sort": "date"}

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
                        date = item['pubDate'][:16]
                        
                        with st.expander(f"{title}"):
                            st.caption(f"📅 {date}")
                            st.write(desc)
                            st.link_button("기사 원문 읽기", link)
                else:
                    st.info("검색 결과가 없습니다.")
            elif response.status_code == 401:
                st.error("❌ 인증 실패: Client ID와 Secret을 확인하세요.")
            else:
                st.error(f"❌ API 오류: {response.status_code}")
                
        except Exception as e:
            st.error(f"❌ 접속 오류 발생: {e}")