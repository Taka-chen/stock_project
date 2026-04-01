from flask import Flask, render_template, request, jsonify
import json, os, datetime, re
import feedparser
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

DATA_DIR = 'data'
WATCHLIST_FILE = os.path.join(DATA_DIR, 'watchlist.json')
PDF_DIR = os.path.join(DATA_DIR, 'pdf_reports')
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)


def load_json(path, default):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────
# Pages
# ─────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        save_json(CONFIG_FILE, request.json)
        return jsonify({'ok': True})
    return jsonify(load_json(CONFIG_FILE, {}))


# ── Tab 1: Watchlist ──────────────────────────────

def _fmt(item):
    """Normalize a quote dict into standard format."""
    sym  = item.get('symbol', '')
    name = item.get('longname') or item.get('shortname') or sym
    market = 'TW' if sym.endswith('.TW') or sym.endswith('.TWO') else 'US'
    return {'symbol': sym, 'name': name,
            'exchange': item.get('exchange', ''),
            'market': market,
            'type': item.get('quoteType', 'EQUITY')}


@app.route('/api/search')
def search_stock():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    # Method 1: yfinance Search
    try:
        import yfinance as yf
        s = yf.Search(q, max_results=10, enable_fuzzy_query=True)
        quotes = getattr(s, 'quotes', [])
        results = [_fmt(i) for i in quotes if i.get('quoteType') in ('EQUITY', 'ETF')]
        if results:
            print(f'[search] yfinance OK: {len(results)} for "{q}"')
            return jsonify(results)
    except Exception as e:
        print(f'[search] yfinance failed: {e}')

    # Method 2: Yahoo REST API (try query2 then query1)
    for host in ('query2.finance.yahoo.com', 'query1.finance.yahoo.com'):
        try:
            url = (f'https://{host}/v1/finance/search'
                   f'?q={requests.utils.quote(q)}&quotesCount=10&newsCount=0')
            hdrs = {
                'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                               'AppleWebKit/537.36 (KHTML, like Gecko) '
                               'Chrome/124.0.0.0 Safari/537.36'),
                'Accept': 'application/json',
                'Referer': 'https://finance.yahoo.com/',
            }
            r = requests.get(url, headers=hdrs, timeout=8)
            if r.status_code == 200:
                results = [_fmt(i) for i in r.json().get('quotes', [])
                           if i.get('quoteType') in ('EQUITY', 'ETF')]
                if results:
                    print(f'[search] REST OK ({host}): {len(results)}')
                    return jsonify(results)
        except Exception as e:
            print(f'[search] REST failed ({host}): {e}')

    # Method 3: Direct ticker lookup
    try:
        import yfinance as yf
        candidates = [q.upper(), q.upper() + '.TW', q.upper() + '.TWO']
        results = []
        for sym in candidates:
            try:
                t = yf.Ticker(sym)
                fi = t.fast_info
                if getattr(fi, 'last_price', None):
                    ti = t.info
                    name = ti.get('longName') or ti.get('shortName', sym)
                    market = 'TW' if sym.endswith('.TW') or sym.endswith('.TWO') else 'US'
                    results.append({'symbol': sym, 'name': name,
                                    'exchange': ti.get('exchange', ''),
                                    'market': market, 'type': 'EQUITY'})
            except Exception:
                pass
        if results:
            return jsonify(results)
    except Exception as e:
        print(f'[search] direct lookup failed: {e}')

    return jsonify({'error': f'無法搜尋「{q}」，請嘗試直接輸入代號（如 2330.TW 或 AAPL）'}), 500


@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    wl = load_json(WATCHLIST_FILE, [])
    try:
        import yfinance as yf
        import pandas as pd
        symbols = [s['symbol'] for s in wl]
        if symbols:
            tickers = symbols[0] if len(symbols) == 1 else symbols
            raw = yf.download(tickers, period='5d', progress=False, auto_adjust=True)
            close = raw['Close'] if 'Close' in raw else None
            if close is not None:
                if isinstance(close, pd.Series):
                    close = close.to_frame(name=symbols[0])
                for stock in wl:
                    sym = stock['symbol']
                    try:
                        prices = close[sym].dropna()
                        stock['price'] = round(float(prices.iloc[-1]), 2)
                        stock['change_pct'] = (
                            round((float(prices.iloc[-1]) - float(prices.iloc[-2]))
                                  / float(prices.iloc[-2]) * 100, 2)
                            if len(prices) >= 2 else 0.0
                        )
                    except Exception:
                        stock['price'] = stock['change_pct'] = None
    except Exception:
        for s in wl:
            s['price'] = s['change_pct'] = None
    return jsonify(wl)


@app.route('/api/watchlist/add', methods=['POST'])
def add_stock():
    stock = request.json
    wl = load_json(WATCHLIST_FILE, [])
    if any(s['symbol'] == stock['symbol'] for s in wl):
        return jsonify({'ok': False, 'msg': '已在清單中'})
    wl.append({k: stock.get(k, '') for k in ('symbol', 'name', 'market', 'exchange', 'type')})
    save_json(WATCHLIST_FILE, wl)
    return jsonify({'ok': True})


@app.route('/api/watchlist/remove', methods=['POST'])
def remove_stock():
    symbol = request.json.get('symbol')
    wl = [s for s in load_json(WATCHLIST_FILE, []) if s['symbol'] != symbol]
    save_json(WATCHLIST_FILE, wl)
    return jsonify({'ok': True})


# ── Tab 2: News & Summarize ───────────────────────

def fetch_google_news(query):
    try:
        url = (f'https://news.google.com/rss/search'
               f'?q={requests.utils.quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant')
        feed = feedparser.parse(url)
        return [{
            'title': e.get('title', ''),
            'link': e.get('link', ''),
            'published': e.get('published', ''),
            'source': 'Google News',
            'summary': BeautifulSoup(e.get('summary', ''), 'html.parser').get_text()[:400]
        } for e in feed.entries[:6]]
    except Exception:
        return []


def fetch_yahoo_news(symbol):
    try:
        feed = feedparser.parse(f'https://finance.yahoo.com/rss/headline?s={symbol}')
        return [{
            'title': e.get('title', ''),
            'link': e.get('link', ''),
            'published': e.get('published', ''),
            'source': 'Yahoo Finance',
            'summary': BeautifulSoup(e.get('summary', ''), 'html.parser').get_text()[:400]
        } for e in feed.entries[:5]]
    except Exception:
        return []


@app.route('/api/news', methods=['POST'])
def get_news():
    stocks = request.json.get('stocks', [])
    result = {}
    for stock in stocks:
        sym = stock['symbol']
        query = f'股票{stock.get("name", sym)} {sym} 最新新聞'
        result[sym] = {
            'stock': stock,
            'articles': fetch_google_news(query) + fetch_yahoo_news(sym)
        }
    return jsonify(result)


def _ai_call(api_key, prompt, max_tokens=900):
    """
    支援 Groq 和 Gemini 兩種 API Key，自動判斷並呼叫。
    - Groq Key 格式：gsk_...
    - Gemini Key 格式：AIzaSy...
    """
    if api_key.startswith('gsk_'):
        return _groq_call(api_key, prompt, max_tokens)
    else:
        return _gemini_rest_call(api_key, prompt, max_tokens)


def _groq_call(api_key, prompt, max_tokens=900):
    """Groq API - 免費且快速（每天 14400 次請求）。"""
    models = ['llama-3.3-70b-versatile', 'llama3-8b-8192', 'mixtral-8x7b-32768']
    last_err = None
    for model in models:
        try:
            r = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={'Authorization': f'Bearer {api_key}',
                         'Content-Type': 'application/json'},
                json={'model': model,
                      'messages': [{'role': 'user', 'content': prompt}],
                      'max_tokens': max_tokens, 'temperature': 0.7},
                timeout=60
            )
            data = r.json()
            if r.status_code == 200:
                text = data['choices'][0]['message']['content']
                print(f'[groq] 成功使用: {model}')
                return text
            err_msg = data.get('error', {}).get('message', str(data))
            print(f'[groq] {model} 失敗: {err_msg[:120]}')
            last_err = err_msg
        except Exception as e:
            print(f'[groq] {model} 例外: {e}')
            last_err = str(e)
    raise Exception(f'Groq 失敗：{last_err}')


def _gemini_rest_call(api_key, prompt, max_tokens=900):
    """Gemini REST API（需在 aistudio.google.com 建立的 Key 才有免費額度）。"""
    models = ['gemini-1.5-flash', 'gemini-1.5-flash-8b']
    last_err = None
    for model in models:
        url = (f'https://generativelanguage.googleapis.com/v1beta/models/'
               f'{model}:generateContent?key={api_key}')
        try:
            r = requests.post(url, json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'maxOutputTokens': max_tokens, 'temperature': 0.7}
            }, timeout=60)
            data = r.json()
            if r.status_code == 200:
                text = data['candidates'][0]['content']['parts'][0]['text']
                print(f'[gemini] 成功使用: {model}')
                return text
            err_msg = data.get('error', {}).get('message', str(data))
            print(f'[gemini] {model} 失敗({r.status_code}): {err_msg[:120]}')
            last_err = err_msg
        except Exception as e:
            print(f'[gemini] {model} 例外: {e}')
            last_err = str(e)
    raise Exception(f'Gemini 失敗（請確認 Key 是在 aistudio.google.com 建立的）：{last_err}')


@app.route('/api/summarize', methods=['POST'])
def summarize():
    data = request.json
    api_key = data.get('api_key', '').strip()
    news_data = data.get('news_data', {})

    if not api_key:
        return jsonify({'error': '請先在右上角⚙️設定中輸入 Gemini API Key'}), 400

    summaries = {}
    for symbol, info in news_data.items():
        articles = info.get('articles', [])
        stock = info.get('stock', {})

        if not articles:
            summaries[symbol] = '⚠️ 無法取得新聞資料，請確認網路連線或股票代號。'
            continue

        news_text = '\n'.join(
            f'[{a["source"]}] {a["title"]}\n{a.get("summary", "")}'
            for a in articles
        )

        prompt = f"""你是專業股票分析師，請根據 {stock.get('name', symbol)}（{symbol}）的最新市場新聞和財務數據以及其他你所能找到的公司基本面信息進行分析。
                    所有的回答內容都請附上的參考的資料引用來源
                    請以繁體中文輸出（Markdown 格式）：

                    ### 📊 市場動態摘要
                    （精準描述當前市場動態）

                    ### 🔑 關鍵事件
                   （列出近期最重要的新聞事件最多10條以下，並說明其內容和影響）

                    ### 📈 股價影響分析
                    **正面因素：** ...
                    **負面因素：** ...

                    ### ⚠️ 風險提示
                    - 風險一

                    資訊要具體精準，避免模糊用語。"""

        try:
            summaries[symbol] = _ai_call(api_key, prompt, max_tokens=900)
        except Exception as e:
            summaries[symbol] = f'⚠️ 分析失敗：{e}'

    return jsonify(summaries)


@app.route('/api/export_pdf', methods=['POST'])
def export_pdf():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    data = request.json
    summaries = data.get('summaries', {})
    news_data = data.get('news_data', {})

    date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = os.path.join(PDF_DIR, f'stock_report_{date_str}.pdf')

    # ── 字體偵測：優先使用專案內字體，兼容 macOS / Windows / Linux ──
    font_name = 'Helvetica'
    font_candidates = [
        # 專案內（最優先，跨平台通用）→ 下載後放 data/ 即可
        'data/NotoSansSC-Regular.ttf',

        # macOS
        '/System/Library/Fonts/Supplemental/Arial Unicode MS.ttf',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/Library/Fonts/Arial Unicode MS.ttf',

        # Windows（繁體優先）
        'C:/Windows/Fonts/msjh.ttf',     # 微軟正黑體（繁體中文）
        'C:/Windows/Fonts/msjhbd.ttf',   # 微軟正黑體 Bold
        'C:/Windows/Fonts/mingliu.ttc',  # 新細明體
        'C:/Windows/Fonts/msyh.ttf',     # 微軟雅黑（簡體）
        'C:/Windows/Fonts/msyhbd.ttc',

        # Linux
        '/usr/share/fonts/truetype/noto/NotoSansCJKtc-Regular.ttf',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
    ]

    for fp in font_candidates:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont('CJK', fp))
                font_name = 'CJK'
                print(f'[PDF] ✅ 使用字體：{fp}')
                break
            except Exception as e:
                print(f'[PDF] ⚠️ 字體載入失敗：{fp} → {e}')
                continue

    if font_name == 'Helvetica':
        print('[PDF] ❌ 找不到中文字體，建議將 NotoSansSC-Regular.ttf 放入 data/ 資料夾')

    # ── 建立 PDF ──
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            rightMargin=2.2*cm, leftMargin=2.2*cm,
                            topMargin=2.5*cm, bottomMargin=2*cm)

    def sty(n, **kw):
        return ParagraphStyle(n, fontName=font_name, **kw)

    story = []
    now = datetime.datetime.now()
    story += [
        Paragraph('股票資訊日報', sty('T', fontSize=22, spaceAfter=4,
                  textColor=colors.HexColor('#0f172a'), leading=28)),
        Paragraph(f'{now.strftime("%Y 年 %m 月 %d 日  %H:%M")} 由 AI 自動生成',
                  sty('S', fontSize=10, spaceAfter=18, textColor=colors.HexColor('#64748b'))),
        HRFlowable(width='100%', thickness=2.5, color=colors.HexColor('#f59e0b'), spaceAfter=20),
    ]

    for symbol, summary in summaries.items():
        info = news_data.get(symbol, {})
        stock = info.get('stock', {})
        story.append(Paragraph(
            f'{stock.get("name", symbol)}  ({symbol})  [{stock.get("market", "")}]',
            sty('H2', fontSize=14, spaceBefore=18, spaceAfter=8,
                textColor=colors.HexColor('#b45309'))
        ))
        clean = re.sub(r'#{1,4}\s*', '', summary)
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', clean)
        clean = re.sub(r'\*(.+?)\*', r'\1', clean)
        for line in clean.split('\n'):
            if line.strip():
                story.append(Paragraph(line.strip(),
                    sty('B', fontSize=9.5, leading=17, spaceAfter=3,
                        textColor=colors.HexColor('#1e293b'))))
        story.append(Spacer(1, 6))
        story.append(Paragraph('新聞來源：',
                     sty('SR', fontSize=8, leading=13, textColor=colors.HexColor('#94a3b8'))))
        for a in info.get('articles', [])[:5]:
            story.append(Paragraph(f'[{a["source"]}] {a.get("title","")[:90]}',
                sty('SR2', fontSize=8, leading=13, spaceAfter=2,
                    textColor=colors.HexColor('#94a3b8'))))
        story.append(HRFlowable(width='100%', thickness=0.5,
                                color=colors.HexColor('#e2e8f0'),
                                spaceBefore=14, spaceAfter=2))

    story += [
        Spacer(1, 22),
        Paragraph('免責聲明：本報告由 AI 自動生成，僅供資訊參考，不構成投資建議。投資有風險，請謹慎評估。',
                  sty('D', fontSize=8, leading=13, textColor=colors.HexColor('#94a3b8')))
    ]

    doc.build(story)
    return jsonify({'ok': True, 'filename': os.path.basename(filepath),
                    'path': os.path.abspath(filepath)})


# ── Tab 3: Stock Screening ────────────────────────

SCREEN_TAGS = {
    'industry': [
        '科技/半導體', 'AI/雲端運算', '金融/銀行保險', '醫療/生技製藥',
        '能源/綠能', '消費/零售電商', '工業/自動化', '電動車/汽車供應鏈',
        '不動產/REITs', '原物料/農業'
    ],
    'strategy': [
        '高成長股', '深度價值股', '高股息收益', '動能強勢股',
        '逆勢佈局', '景氣循環股', '防禦型穩健', '小型潛力股',
        '機構低持股', 'ESG永續投資'
    ],
    'technical': [
        '突破歷史新高', '均線多頭排列', 'RSI超賣反彈', 'MACD黃金交叉',
        '底部確認打底', '強勢整理蓄勢', '量增價漲', '週線轉強訊號'
    ],
    'risk': [
        '保守穩健（低波動）', '平衡配置（中風險）',
        '積極成長（高風險）', '高風險高報酬（投機型）'
    ],
    'horizon': [
        '短線（1-4週）', '中線（1-3月）', '長線（6月以上）', '波段操作'
    ]
}


@app.route('/api/screen_tags')
def get_screen_tags():
    return jsonify(SCREEN_TAGS)


@app.route('/api/screen', methods=['POST'])
def screen_stocks():
    data = request.json
    api_key = data.get('api_key', '').strip()
    tags = data.get('tags', {})

    if not api_key:
        return jsonify({'error': '請先在右上角⚙️設定中輸入 Gemini API Key'}), 400
    if not any(tags.values()):
        return jsonify({'error': '請至少選擇一個標籤'}), 400

    lines = []
    labels = {'industry': '目標產業', 'strategy': '投資策略',
              'technical': '技術條件', 'risk': '風險偏好', 'horizon': '操作週期'}
    for k, label in labels.items():
        if tags.get(k):
            lines.append(f'{label}：{" ／ ".join(tags[k])}')
    criteria = '\n'.join(lines)

    prompt = f"""你是頂尖台美股分析師，依照以下投資篩選條件，精選當前最值得關注的標的：

            【篩選條件】
            {criteria}

            請以繁體中文輸出：

            ## 🇹🇼 台股精選（3-4檔）

            ### [代號] 股票名稱
            **推薦核心：** 說明選股邏輯
            **符合條件：** 符合哪些篩選項
            **基本面：** 財務或業務亮點(附上參考來源或理由)
            **技術面：** 當前形態與關鍵價位(附上參考來源或理由)
            **操作週期：** 建議持有時間(附上參考來源或理由)
            **目標區間：** 合理估值參考(附上參考來源或理由)
            **主要風險：** 最需注意的威脅

            （3-4 檔台股）

            ---

            ## 🇺🇸 美股精選（3-4檔）

            （同上格式，3-4 檔美股）

            ---

            ## 📊 整體市場觀點
            （大盤環境分析、資金配置建議、操作紀律提示）

            ---
            ⚠️ 以上為 AI 分析參考，非專業投資建議。"""

    try:
        result = _ai_call(api_key, prompt, max_tokens=2200)
        return jsonify({'result': result, 'criteria': criteria})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    PORT = 5001   # 改這裡可換 port

    print('=' * 52)
    print('  📈 股票資訊助手 Stock Assistant')
    print('=' * 52)
    print(f'  📂 專案路徑 : {os.path.abspath(".")}')
    print(f'  💾 PDF 存放  : {os.path.abspath(PDF_DIR)}')
    print(f'  🌐 請開啟    : http://127.0.0.1:{PORT}')
    print('=' * 52)
    app.run(debug=True, host='127.0.0.1', port=PORT)
