import feedparser
import requests
import re
from googletrans import Translator

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
ai_keywords = ["AI", "人工智能", "机器学习"]
edu_keywords = ["AI教育", "AI教学", "教师", "学生"]

# ===== 翻译工具 =====
translator = Translator()

# ===== 工具函数 =====
def is_match(text, keywords):
    return any(k.lower() in text.lower() for k in keywords)

def clean_text(text):
    text = re.sub(r'<.*?>', '', text)  # 去掉 HTML 标签
    return ' '.join(text.split())       # 去掉多余空格

def translate_to_chinese(text):
    try:
        return translator.translate(text, dest='zh-cn').text
    except:
        return text

def generate_summary(text, max_len=100):
    text = clean_text(text)
    if len(text) > max_len:
        return text[:max_len] + "…"
    return text

def fetch_news():
    news = []
    for url in rss_list:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                news.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.summary if "summary" in entry else "",
                    "published": entry.get("published", "")
                })
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
    return news

def classify_news(news):
    zh_news, en_news, edu_news = [], [], []
    for n in news:
        text = n['title'] + n['summary']
        if is_match(text, ai_keywords):
            if is_match(text, edu_keywords):
                edu_news.append(n)
            elif any(c.isascii() for c in n['title']):
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
    if zh_news:
        for n in zh_news[:10]:
            msg += format_news_item(n, "中文媒体")
    if en_news:
        for n in en_news[:10]:
            msg += format_news_item(n, "海外媒体", translate=True)
    if edu_news:
        for n in edu_news[:10]:
            msg += format_news_item(n, "AI教育新闻")
    return msg

def send_to_feishu(text):
    data = {"msg_type": "text", "content": {"text": text}}
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=data)
        if resp.status_code != 200:
            print("Feishu push failed:", resp.text)
    except Exception as e:
        print("Feishu push error:", e)

def main():
    news = fetch_news()
    zh_news, en_news, edu_news = classify_news(news)
    msg = build_message(zh_news, en_news, edu_news)
    send_to_feishu(msg)

if __name__ == "__main__":
    main()
