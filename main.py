import feedparser
import requests
from datetime import datetime

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

# ===== 工具函数 =====
def is_match(text, keywords):
    return any(k.lower() in text.lower() for k in keywords)

def fetch_news():
    news = []
    for url in rss_list:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:  # 每源前10条
                news.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.summary if "summary" in entry else "",
                    "published": entry.get("published", "")
                })
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            continue
    return news

def classify_news(news):
    zh_news, en_news, edu_news = [], [], []
    for n in news:
        text = n["title"] + n["summary"]
        if is_match(text, ai_keywords):
            if is_match(text, edu_keywords):
                edu_news.append(n)
            elif any(char.isascii() for char in n["title"]):
                en_news.append(n)
            else:
                zh_news.append(n)
    return zh_news, en_news, edu_news

def generate_summary(text, max_len=100):
    # 规则生成摘要：取前 max_len 字，去掉多余空格
    clean_text = ' '.join(text.split())
    if len(clean_text) > max_len:
        return clean_text[:max_len] + "…"
    return clean_text

def build_message(zh_news, en_news, edu_news):
    msg = "📌 今日 AI 新闻摘要\n\n"

    def format_section(news_list, title):
        section = f"【{title}】\n"
        for i, n in enumerate(news_list[:10], 1):
            combined_text = f"{n['title']} {n['summary']} 链接: {n['link']}"
            summary = generate_summary(combined_text, max_len=100)
            section += f"{i}. {summary}\n\n"
        return section

    if zh_news:
        msg += format_section(zh_news, "中文媒体")
    if en_news:
        msg += format_section(en_news, "海外媒体")
    if edu_news:
        msg += format_section(edu_news, "AI教育新闻")
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
