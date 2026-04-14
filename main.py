import feedparser
import requests
import re
from googletrans import Translator
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===== RSS 源 =====
rss_list = [
    "https://techcrunch.com/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://36kr.com/feed-newsflash",
    "https://rss.huxiu.com/",
    "https://ithome.com/rss",
    "https://sspai.com/feed",
    "http://www.geekpark.net/rss",
    "https://rsshub.app/chouti/top/168",
    "https://rsshub.app/zhihu/hotlist",
    "http://feeds.feedburner.com/ruanyifeng",
    "https://www.ifanr.com/feed",
    "https://rsshub.app/juejin/posts/tech",
    "https://rsshub.app/juejin/category/frontend",
    "https://openai.com/news/rss.xml",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "https://www.marktechpost.com/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://blog.google/technology/ai/rss/",
    "https://huggingface.co/blog/feed.xml",
    "https://news.mit.edu/rss/topic/artificial-intelligence2",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://analyticsindiamag.com/feed/",
    "https://ai-techpark.com/category/ai/feed/",
    "https://www.artificialintelligence-news.com/feed/rss/",
    "https://rss.arxiv.org/rss/cs.AI",
    "https://aws.amazon.com/blogs/machine-learning/feed/",
    "https://spectrum.ieee.org/feeds/topic/artificial-intelligence",
    "https://thegradient.pub/rss/",
]

# ===== 飞书 Webhook =====
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/bd733c08-ca3a-4bb5-bcd2-669e14f28579"

# ===== 关键词 =====
ai_main_keywords = ["AI", "人工智能", "机器学习"]
ai_context_keywords = ["深度学习", "神经网络", "算法", "模型", "智能系统", "应用", "architecture", "training"]
edu_keywords = ["AI教育", "AI教学", "教师", "学生"]

translator = Translator()
translation_cache = {}

# ===== 工具函数 =====
def clean_text(text):
    text = re.sub(r'<.*?>', '', text)
    return ' '.join(text.split())

def is_ai_related(text):
    text = clean_text(text)
    return any(k.lower() in text.lower() for k in ai_main_keywords) and any(k.lower() in text.lower() for k in ai_context_keywords)

def is_edu_related(text):
    text = clean_text(text)
    return any(k.lower() in text.lower() for k in edu_keywords)

def translate_to_chinese(text):
    text = clean_text(text)
    if text in translation_cache:
        return translation_cache[text]
    try:
        translated = translator.translate(text, dest='zh-cn').text
        translation_cache[text] = translated
        return translated
    except:
        return text

def generate_summary(text, max_len=100):
    text = clean_text(text)
    return text if len(text) <= max_len else text[:max_len] + "…"

# ===== 并发抓取单个 RSS =====
def fetch_single_rss(url, max_entries=5):
    news = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_entries]:
            news.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.summary if "summary" in entry else "",
                "published": entry.get("published", "")
            })
    except:
        pass
    return news

def fetch_news_concurrent():
    news = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_single_rss, url) for url in rss_list]
        for future in as_completed(futures):
            news.extend(future.result())
    return news

def classify_news(news):
    zh_news, en_news, edu_news = [], [], []
    for n in news:
        combined_text = n['title'] + n['summary']
        if is_edu_related(combined_text):
            edu_news.append(n)
        elif is_ai_related(combined_text):
            if any(c.isascii() for c in n['title']):
                en_news.append(n)
            else:
                zh_news.append(n)
    return zh_news, en_news, edu_news

def format_news_item(news, media_type, translate=False):
    title = clean_text(news['title'])
    summary = clean_text(news['summary'])
    if translate:
        title = translate_to_chinese(title)
        summary = translate_to_chinese(summary)
    summary_text = generate_summary(summary, max_len=100)
    published = news.get('published', '')
    link = news.get('link', '')
    return f"【{media_type}】{title} (来源: {media_type}, 时间: {published})\n{summary_text}\n链接: {link}\n"

def build_message(zh_news, en_news, edu_news):
    msg = "📌 今日 AI 新闻摘要\n\n"
    for n in zh_news[:10]:
        msg += format_news_item(n, "中文媒体")
    # 并发翻译海外新闻
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(format_news_item, n, "海外媒体", True) for n in en_news[:5]]
        for future in as_completed(futures):
            msg += future.result()
    for n in edu_news[:10]:
        msg += format_news_item(n, "AI教育新闻")
    return msg

def send_to_feishu(text):
    data = {"msg_type": "text", "content": {"text": text}}
    try:
        requests.post(FEISHU_WEBHOOK, json=data)
    except:
        pass

def main():
    news = fetch_news_concurrent()
    zh_news, en_news, edu_news = classify_news(news)
    msg = build_message(zh_news, en_news, edu_news)
    send_to_feishu(msg)

if __name__ == "__main__":
    main()
