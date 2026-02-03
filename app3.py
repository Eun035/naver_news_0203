import streamlit as st
import requests
import yfinance as yf
import pandas as pd

# ============================================
# 1️⃣ 페이지 기본 설정
# ============================================
st.set_page_config(
    page_title="경제 뉴스 & 금 한돈 시세",
    page_icon="🇰🇷",
    layout="centered"
)

# ============================================
# 2️⃣ 데이터 처리 함수 (단위 변환 추가)
# ============================================
def get_current_price(ticker_symbol):
    """
    특정 티커의 현재가와 전일 대비 변동액을 가져옵니다.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="1d", interval="1m")
        
        if df.empty:
            df = ticker.history(period="5d") # 장 마감 시 최근 데이터 사용
        
        if df.empty:
            return None, None

        last_row = df.iloc[-1]
        current_price = last_row['Close']
        open_price = df.iloc[0]['Open']
        delta = current_price - open_price
        
        return current_price, delta

    except Exception:
        return None, None

def get_market_data():
    """
    환율, 금, 은 데이터를 가져와 '1돈(3.75g)' 기준으로 변환합니다.
    """
    # 상수 정의
    OZ_TO_GRAM = 31.1034768  # 1 트로이온스 = 약 31.1g
    DON_GRAM = 3.75          # 1돈 = 3.75g

    # 1. 데이터 가져오기 (따로 호출하여 안정성 확보)
    rate_now, rate_delta = get_current_price('KRW=X') # 환율
    gold_oz, gold_delta_oz = get_current_price('GC=F') # 금(온스)
    silver_oz, silver_delta_oz = get_current_price('SI=F') # 은(온스)

    if rate_now is None or gold_oz is None or silver_oz is None:
        return None

    # 2. 단위 변환 계산 (온스 -> 그램 -> 돈)
    # 금값 계산
    gold_g_usd = gold_oz / OZ_TO_GRAM            # 1g당 달러
    gold_don_usd = gold_g_usd * DON_GRAM         # 1돈당 달러
    gold_don_krw = gold_don_usd * rate_now       # 1돈당 원화 (최종)

    # 금 변동폭 계산 (근사치)
    gold_delta_don_usd = (gold_delta_oz / OZ_TO_GRAM) * DON_GRAM
    gold_delta_krw = gold_delta_don_usd * rate_now

    # 은값 계산
    silver_g_usd = silver_oz / OZ_TO_GRAM
    silver_don_usd = silver_g_usd * DON_GRAM
    silver_don_krw = silver_don_usd * rate_now

    # 은 변동폭 계산
    silver_delta_don_usd = (silver_delta_oz / OZ_TO_GRAM) * DON_GRAM
    silver_delta_krw = silver_delta_don_usd * rate_now

    return {
        "rate_now": rate_now,
        "rate_delta": rate_delta,
        "gold_don_krw": gold_don_krw,      # 금 1돈 가격
        "gold_delta": gold_delta_krw,
        "silver_don_krw": silver_don_krw,  # 은 1돈 가격
        "silver_delta": silver_delta_krw,
        "gold_oz_usd": gold_oz             # (참고용) 국제 시세
    }

def clean_title(title):
    title = title.replace("<b>", "").replace("</b>", "")
    title = title.replace("&quot;", "\"").replace("&lt;", "<").replace("&gt;", ">")
    return title

# ============================================
# 3️⃣ 사이드바: 설정
# ============================================
with st.sidebar:
    st.header("⚙️ 설정")
    client_id = st.text_input("Client ID", type="password")
    client_secret = st.text_input("Client Secret", type="password")
    st.info("뉴스 검색을 위해 API 키가 필요합니다.")

# ============================================
# 4️⃣ 메인 화면: 시장 지표
# ============================================
st.title("🇰🇷 오늘의 시장 & 뉴스")
st.markdown("실시간 환율과 **금·은 한 돈(3.75g)** 기준 가격입니다.")

with st.spinner('시장 데이터를 분석 중입니다...'):
    market_data = get_market_data()

st.subheader("💰 실시간 시세 (한 돈 기준)")

col1, col2, col3 = st.columns(3)

if market_data:
    # 1. 환율
    with col1:
        st.metric(
            label="🇺🇸 원/달러 환율",
            value=f"{market_data['rate_now']:,.2f} 원",
            delta=f"{market_data['rate_delta']:.2f} 원"
        )
    
    # 2. 금 (1돈)
    with col2:
        st.metric(
            label="🥇 금 1돈 (3.75g)",
            value=f"{market_data['gold_don_krw']:,.0f} 원",
            delta=f"{market_data['gold_delta']:.0f} 원"
        )
        st.caption(f"국제시세: ${market_data['gold_oz_usd']:.2f}/oz")

    # 3. 은 (1돈)
    with col3:
        st.metric(
            label="🥈 은 1돈 (3.75g)",
            value=f"{market_data['silver_don_krw']:,.0f} 원",
            delta=f"{market_data['silver_delta']:.0f} 원"
        )
        st.caption("※ 부가세/공임비 제외 기준")
    
    st.markdown("---")
    st.info("💡 위 가격은 국제 원자재 가격을 환율 계산하여 '1돈'으로 환산한 수치입니다. **실제 금은방 소매가(부가세+수수료 포함)는 이보다 더 높습니다.**")

else:
    st.warning("📉 현재 시장 데이터를 불러올 수 없습니다.")
    st.markdown("---")


# ============================================
# 5️⃣ 메인 화면: 뉴스 검색
# ============================================
st.subheader("📰 관련 뉴스 검색")

search_col, btn_col = st.columns([4, 1])
with search_col:
    keyword = st.text_input("검색어", placeholder="예: 금값 전망, 경제 위기")
with btn_col:
    st.write("") 
    st.write("")
    search_btn = st.button("검색", type="primary")

if search_btn:
    if not client_id or not client_secret:
        st.error("🔒 사이드바에 API 키를 입력해주세요.")
        st.stop()
    if not keyword:
        st.warning("⚠️ 검색어를 입력해주세요.")
        st.stop()

    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    params = {"query": keyword, "display": 5, "sort": "date"}

    with st.spinner(f"'{keyword}' 뉴스 검색 중..."):
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
                        
                        with st.expander(title):
                            st.caption(date)
                            st.write(desc)
                            st.link_button("기사 원문", link)
                else:
                    st.info("검색 결과가 없습니다.")
            else:
                st.error("API 호출 오류가 발생했습니다.")
        except Exception as e:
            st.error(f"오류: {e}")