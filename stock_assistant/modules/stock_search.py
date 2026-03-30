# -*- coding: utf-8 -*-
"""
Stock search module with comprehensive TW and US stock databases.
Supports searching by ticker symbol or company name.
"""

import re

# ── 台股資料庫（主要上市/上櫃股票）──
TW_STOCKS = [
    # 半導體
    {"ticker": "2330", "name": "台積電", "market": "TW", "sector": "半導體"},
    {"ticker": "2454", "name": "聯發科", "market": "TW", "sector": "半導體"},
    {"ticker": "2303", "name": "聯電", "market": "TW", "sector": "半導體"},
    {"ticker": "3711", "name": "日月光投控", "market": "TW", "sector": "半導體"},
    {"ticker": "2344", "name": "華邦電", "market": "TW", "sector": "半導體"},
    {"ticker": "3034", "name": "聯詠", "market": "TW", "sector": "半導體"},
    {"ticker": "2379", "name": "瑞昱", "market": "TW", "sector": "半導體"},
    {"ticker": "6770", "name": "力積電", "market": "TW", "sector": "半導體"},
    {"ticker": "3529", "name": "力旺", "market": "TW", "sector": "半導體"},
    {"ticker": "2337", "name": "旺宏", "market": "TW", "sector": "半導體"},
    {"ticker": "6239", "name": "力成", "market": "TW", "sector": "半導體"},
    {"ticker": "2408", "name": "南亞科", "market": "TW", "sector": "半導體"},
    {"ticker": "3443", "name": "創意", "market": "TW", "sector": "半導體"},
    {"ticker": "2449", "name": "京元電子", "market": "TW", "sector": "半導體"},
    {"ticker": "5274", "name": "信驊", "market": "TW", "sector": "半導體"},
    {"ticker": "6197", "name": "佳邦", "market": "TW", "sector": "半導體"},
    {"ticker": "3661", "name": "世芯-KY", "market": "TW", "sector": "半導體"},
    # 電子/科技
    {"ticker": "2317", "name": "鴻海", "market": "TW", "sector": "電子製造"},
    {"ticker": "2382", "name": "廣達", "market": "TW", "sector": "電子製造"},
    {"ticker": "2357", "name": "華碩", "market": "TW", "sector": "電子製造"},
    {"ticker": "2353", "name": "宏碁", "market": "TW", "sector": "電子製造"},
    {"ticker": "2308", "name": "台達電", "market": "TW", "sector": "電子零件"},
    {"ticker": "2327", "name": "國巨", "market": "TW", "sector": "電子零件"},
    {"ticker": "2395", "name": "研華", "market": "TW", "sector": "電子製造"},
    {"ticker": "6669", "name": "緯穎", "market": "TW", "sector": "電子製造"},
    {"ticker": "3017", "name": "奇鋐", "market": "TW", "sector": "電子零件"},
    {"ticker": "3008", "name": "大立光", "market": "TW", "sector": "光學"},
    {"ticker": "2474", "name": "可成", "market": "TW", "sector": "電子製造"},
    {"ticker": "2458", "name": "義隆", "market": "TW", "sector": "IC設計"},
    {"ticker": "6547", "name": "高端疫苗", "market": "TW", "sector": "生技"},
    {"ticker": "2376", "name": "技嘉", "market": "TW", "sector": "電子製造"},
    {"ticker": "2360", "name": "致茂", "market": "TW", "sector": "電子製造"},
    {"ticker": "3231", "name": "緯創", "market": "TW", "sector": "電子製造"},
    {"ticker": "2356", "name": "英業達", "market": "TW", "sector": "電子製造"},
    {"ticker": "3714", "name": "富采", "market": "TW", "sector": "LED"},
    {"ticker": "2383", "name": "台光電", "market": "TW", "sector": "電子零件"},
    {"ticker": "6415", "name": "矽力-KY", "market": "TW", "sector": "半導體"},
    {"ticker": "4938", "name": "和碩", "market": "TW", "sector": "電子製造"},
    {"ticker": "2301", "name": "光寶科", "market": "TW", "sector": "電子製造"},
    {"ticker": "2迴避", "name": "群創", "market": "TW", "sector": "面板"},
    {"ticker": "3481", "name": "群創", "market": "TW", "sector": "面板"},
    {"ticker": "2409", "name": "友達", "market": "TW", "sector": "面板"},
    # 金融
    {"ticker": "2882", "name": "國泰金", "market": "TW", "sector": "金融"},
    {"ticker": "2886", "name": "兆豐金", "market": "TW", "sector": "金融"},
    {"ticker": "2891", "name": "中信金", "market": "TW", "sector": "金融"},
    {"ticker": "2881", "name": "富邦金", "market": "TW", "sector": "金融"},
    {"ticker": "5880", "name": "合庫金", "market": "TW", "sector": "金融"},
    {"ticker": "2884", "name": "玉山金", "market": "TW", "sector": "金融"},
    {"ticker": "2885", "name": "元大金", "market": "TW", "sector": "金融"},
    {"ticker": "2892", "name": "第一金", "market": "TW", "sector": "金融"},
    {"ticker": "2880", "name": "華南金", "market": "TW", "sector": "金融"},
    {"ticker": "2883", "name": "開發金", "market": "TW", "sector": "金融"},
    {"ticker": "2887", "name": "台新金", "market": "TW", "sector": "金融"},
    {"ticker": "2890", "name": "永豐金", "market": "TW", "sector": "金融"},
    {"ticker": "2801", "name": "彰銀", "market": "TW", "sector": "金融"},
    {"ticker": "2834", "name": "臺企銀", "market": "TW", "sector": "金融"},
    {"ticker": "6005", "name": "群益證", "market": "TW", "sector": "金融"},
    {"ticker": "2888", "name": "新光金", "market": "TW", "sector": "金融"},
    # 電信
    {"ticker": "2412", "name": "中華電", "market": "TW", "sector": "電信"},
    {"ticker": "3045", "name": "台灣大", "market": "TW", "sector": "電信"},
    {"ticker": "4904", "name": "遠傳", "market": "TW", "sector": "電信"},
    # 石化/傳產
    {"ticker": "6505", "name": "台塑化", "market": "TW", "sector": "石化"},
    {"ticker": "1301", "name": "台塑", "market": "TW", "sector": "石化"},
    {"ticker": "1303", "name": "南亞", "market": "TW", "sector": "石化"},
    {"ticker": "1326", "name": "台化", "market": "TW", "sector": "石化"},
    {"ticker": "2002", "name": "中鋼", "market": "TW", "sector": "鋼鐵"},
    {"ticker": "1402", "name": "遠東新", "market": "TW", "sector": "紡織"},
    {"ticker": "1101", "name": "台泥", "market": "TW", "sector": "水泥"},
    {"ticker": "1102", "name": "亞泥", "market": "TW", "sector": "水泥"},
    # 汽車/運輸
    {"ticker": "2207", "name": "和泰車", "market": "TW", "sector": "汽車"},
    {"ticker": "2105", "name": "正新", "market": "TW", "sector": "橡膠"},
    {"ticker": "2603", "name": "長榮", "market": "TW", "sector": "航運"},
    {"ticker": "2609", "name": "陽明", "market": "TW", "sector": "航運"},
    {"ticker": "2615", "name": "萬海", "market": "TW", "sector": "航運"},
    # 食品/零售
    {"ticker": "1216", "name": "統一", "market": "TW", "sector": "食品"},
    {"ticker": "2912", "name": "統一超", "market": "TW", "sector": "零售"},
    {"ticker": "2915", "name": "潤泰全", "market": "TW", "sector": "零售"},
    # 生技醫療
    {"ticker": "4711", "name": "中裕", "market": "TW", "sector": "生技"},
    {"ticker": "6505", "name": "台塑化", "market": "TW", "sector": "石化"},
    {"ticker": "1795", "name": "美時", "market": "TW", "sector": "製藥"},
    # AI/雲端相關新秀
    {"ticker": "6886", "name": "華特科", "market": "TW", "sector": "AI"},
    {"ticker": "6533", "name": "晶心科", "market": "TW", "sector": "AI/半導體"},
    {"ticker": "3030", "name": "晶相光", "market": "TW", "sector": "AI/光學"},
    {"ticker": "6781", "name": "AES-KY", "market": "TW", "sector": "AI"},
]

# ── 美股資料庫（主要標的）──
US_STOCKS = [
    # 科技巨頭
    {"ticker": "AAPL", "name": "Apple", "market": "US", "sector": "科技"},
    {"ticker": "MSFT", "name": "Microsoft", "market": "US", "sector": "科技"},
    {"ticker": "GOOGL", "name": "Alphabet (Google)", "market": "US", "sector": "科技"},
    {"ticker": "AMZN", "name": "Amazon", "market": "US", "sector": "科技/電商"},
    {"ticker": "META", "name": "Meta Platforms", "market": "US", "sector": "社群媒體"},
    {"ticker": "TSLA", "name": "Tesla", "market": "US", "sector": "電動車"},
    {"ticker": "NVDA", "name": "NVIDIA", "market": "US", "sector": "AI/半導體"},
    {"ticker": "AVGO", "name": "Broadcom", "market": "US", "sector": "半導體"},
    {"ticker": "TSM", "name": "TSMC (ADR)", "market": "US", "sector": "半導體"},
    {"ticker": "AMD", "name": "Advanced Micro Devices", "market": "US", "sector": "半導體"},
    {"ticker": "INTC", "name": "Intel", "market": "US", "sector": "半導體"},
    {"ticker": "QCOM", "name": "Qualcomm", "market": "US", "sector": "半導體"},
    {"ticker": "TXN", "name": "Texas Instruments", "market": "US", "sector": "半導體"},
    {"ticker": "ARM", "name": "ARM Holdings", "market": "US", "sector": "半導體"},
    {"ticker": "ASML", "name": "ASML Holding", "market": "US", "sector": "半導體設備"},
    {"ticker": "AMAT", "name": "Applied Materials", "market": "US", "sector": "半導體設備"},
    {"ticker": "MU", "name": "Micron Technology", "market": "US", "sector": "記憶體"},
    {"ticker": "SMCI", "name": "Super Micro Computer", "market": "US", "sector": "AI伺服器"},
    # 軟體/雲端
    {"ticker": "ORCL", "name": "Oracle", "market": "US", "sector": "企業軟體"},
    {"ticker": "CRM", "name": "Salesforce", "market": "US", "sector": "雲端CRM"},
    {"ticker": "ADBE", "name": "Adobe", "market": "US", "sector": "創意軟體"},
    {"ticker": "SNOW", "name": "Snowflake", "market": "US", "sector": "雲端資料"},
    {"ticker": "PLTR", "name": "Palantir", "market": "US", "sector": "AI/數據分析"},
    {"ticker": "NOW", "name": "ServiceNow", "market": "US", "sector": "企業IT"},
    {"ticker": "WDAY", "name": "Workday", "market": "US", "sector": "HR軟體"},
    {"ticker": "DDOG", "name": "Datadog", "market": "US", "sector": "雲端監控"},
    {"ticker": "NET", "name": "Cloudflare", "market": "US", "sector": "網路安全"},
    {"ticker": "CRWD", "name": "CrowdStrike", "market": "US", "sector": "網路安全"},
    {"ticker": "ZS", "name": "Zscaler", "market": "US", "sector": "網路安全"},
    {"ticker": "PANW", "name": "Palo Alto Networks", "market": "US", "sector": "網路安全"},
    # 電商/消費
    {"ticker": "NFLX", "name": "Netflix", "market": "US", "sector": "串流媒體"},
    {"ticker": "SPOT", "name": "Spotify", "market": "US", "sector": "音樂串流"},
    {"ticker": "UBER", "name": "Uber", "market": "US", "sector": "共享經濟"},
    {"ticker": "LYFT", "name": "Lyft", "market": "US", "sector": "共享經濟"},
    {"ticker": "SHOP", "name": "Shopify", "market": "US", "sector": "電商平台"},
    {"ticker": "MELI", "name": "MercadoLibre", "market": "US", "sector": "拉美電商"},
    # 金融/支付
    {"ticker": "JPM", "name": "JPMorgan Chase", "market": "US", "sector": "銀行"},
    {"ticker": "BAC", "name": "Bank of America", "market": "US", "sector": "銀行"},
    {"ticker": "GS", "name": "Goldman Sachs", "market": "US", "sector": "投資銀行"},
    {"ticker": "MS", "name": "Morgan Stanley", "market": "US", "sector": "投資銀行"},
    {"ticker": "V", "name": "Visa", "market": "US", "sector": "支付"},
    {"ticker": "MA", "name": "Mastercard", "market": "US", "sector": "支付"},
    {"ticker": "PYPL", "name": "PayPal", "market": "US", "sector": "金融科技"},
    {"ticker": "SQ", "name": "Block (Square)", "market": "US", "sector": "金融科技"},
    {"ticker": "BRK-B", "name": "Berkshire Hathaway B", "market": "US", "sector": "多元化"},
    # 醫療
    {"ticker": "UNH", "name": "UnitedHealth Group", "market": "US", "sector": "醫療保險"},
    {"ticker": "JNJ", "name": "Johnson & Johnson", "market": "US", "sector": "醫療"},
    {"ticker": "LLY", "name": "Eli Lilly", "market": "US", "sector": "製藥"},
    {"ticker": "PFE", "name": "Pfizer", "market": "US", "sector": "製藥"},
    {"ticker": "ABBV", "name": "AbbVie", "market": "US", "sector": "生物製藥"},
    {"ticker": "MRK", "name": "Merck", "market": "US", "sector": "製藥"},
    {"ticker": "TMO", "name": "Thermo Fisher Scientific", "market": "US", "sector": "生命科學"},
    {"ticker": "ISRG", "name": "Intuitive Surgical", "market": "US", "sector": "醫療器材"},
    # 消費/零售
    {"ticker": "WMT", "name": "Walmart", "market": "US", "sector": "零售"},
    {"ticker": "COST", "name": "Costco", "market": "US", "sector": "零售"},
    {"ticker": "TGT", "name": "Target", "market": "US", "sector": "零售"},
    {"ticker": "HD", "name": "Home Depot", "market": "US", "sector": "家居零售"},
    {"ticker": "MCD", "name": "McDonald's", "market": "US", "sector": "餐飲"},
    {"ticker": "SBUX", "name": "Starbucks", "market": "US", "sector": "餐飲"},
    {"ticker": "NKE", "name": "Nike", "market": "US", "sector": "運動用品"},
    # 能源
    {"ticker": "XOM", "name": "ExxonMobil", "market": "US", "sector": "石油"},
    {"ticker": "CVX", "name": "Chevron", "market": "US", "sector": "石油"},
    {"ticker": "ENPH", "name": "Enphase Energy", "market": "US", "sector": "太陽能"},
    {"ticker": "NEE", "name": "NextEra Energy", "market": "US", "sector": "再生能源"},
    # 汽車
    {"ticker": "F", "name": "Ford Motor", "market": "US", "sector": "汽車"},
    {"ticker": "GM", "name": "General Motors", "market": "US", "sector": "汽車"},
    {"ticker": "RIVN", "name": "Rivian", "market": "US", "sector": "電動車"},
    {"ticker": "LCID", "name": "Lucid Group", "market": "US", "sector": "電動車"},
    # 通訊/媒體
    {"ticker": "VZ", "name": "Verizon", "market": "US", "sector": "電信"},
    {"ticker": "T", "name": "AT&T", "market": "US", "sector": "電信"},
    {"ticker": "DIS", "name": "Walt Disney", "market": "US", "sector": "娛樂媒體"},
    {"ticker": "CMCSA", "name": "Comcast", "market": "US", "sector": "媒體電信"},
    # 其他大型股
    {"ticker": "PG", "name": "Procter & Gamble", "market": "US", "sector": "消費品"},
    {"ticker": "KO", "name": "Coca-Cola", "market": "US", "sector": "飲料"},
    {"ticker": "PEP", "name": "PepsiCo", "market": "US", "sector": "飲料/食品"},
    {"ticker": "CSCO", "name": "Cisco Systems", "market": "US", "sector": "網路設備"},
    {"ticker": "IBM", "name": "IBM", "market": "US", "sector": "企業IT"},
    {"ticker": "GE", "name": "GE Aerospace", "market": "US", "sector": "航太"},
    {"ticker": "RTX", "name": "RTX (Raytheon)", "market": "US", "sector": "國防"},
    {"ticker": "LMT", "name": "Lockheed Martin", "market": "US", "sector": "國防"},
    {"ticker": "BA", "name": "Boeing", "market": "US", "sector": "航太"},
    {"ticker": "CAT", "name": "Caterpillar", "market": "US", "sector": "重工業"},
    {"ticker": "DE", "name": "Deere & Company", "market": "US", "sector": "農業機械"},
]


def normalize_tw_ticker(ticker: str) -> str:
    """Strip .TW suffix if present and return bare number."""
    return ticker.upper().replace(".TW", "").strip()


def search_stocks(query: str, market: str = "both") -> list:
    """
    Search stocks by ticker or name.
    market: 'TW', 'US', or 'both'
    Returns list of matching stock dicts.
    """
    if not query or len(query) < 1:
        return []

    query_clean = query.strip()
    query_lower = query_clean.lower()
    results = []

    # Build the pool
    pool = []
    if market in ("both", "TW"):
        pool.extend(TW_STOCKS)
    if market in ("both", "US"):
        pool.extend(US_STOCKS)

    seen_tickers = set()

    for stock in pool:
        ticker = stock["ticker"]
        name = stock["name"]

        # Skip duplicates
        if ticker in seen_tickers:
            continue

        match = False

        # Ticker match (case-insensitive, also strip .TW for TW stocks)
        ticker_bare = normalize_tw_ticker(ticker) if stock["market"] == "TW" else ticker.upper()
        if query_lower in ticker.lower() or query_lower in ticker_bare.lower():
            match = True

        # Name match (partial, case-insensitive)
        if query_lower in name.lower():
            match = True

        # For TW stocks: allow searching by number only
        if stock["market"] == "TW" and re.match(r"^\d+$", query_clean):
            if query_clean in ticker_bare:
                match = True

        if match:
            results.append({
                "ticker": ticker,
                "name": name,
                "market": stock["market"],
                "sector": stock.get("sector", ""),
                "display_ticker": f"{ticker_bare}.TW" if stock["market"] == "TW" else ticker,
            })
            seen_tickers.add(ticker)

        if len(results) >= 20:
            break

    # Sort: exact matches first
    def sort_key(s):
        t = normalize_tw_ticker(s["ticker"]) if s["market"] == "TW" else s["ticker"]
        exact_ticker = query_lower == t.lower()
        exact_name = query_lower == s["name"].lower()
        starts_ticker = t.lower().startswith(query_lower)
        starts_name = s["name"].lower().startswith(query_lower)
        return (not exact_ticker, not exact_name, not starts_ticker, not starts_name)

    results.sort(key=sort_key)
    return results[:15]
