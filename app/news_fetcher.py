import requests
import json

API_KEY = "a8cbf20f066445958b2ba9892f9933a2"  

def fetch_headlines(query="technology", language="en", page_size=10):
    url = f"https://newsapi.org/v2/everything?q={query}&language={language}&pageSize={page_size}&apiKey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    articles = []
    if data["status"] == "ok":
        for article in data["articles"]:
            articles.append({
                "title": article["title"],
                "description": article["description"],
                "content": article["content"],
                "url": article["url"]
            })

    return articles

if __name__ == "__main__":
    news = fetch_headlines("mental health")
    print(json.dumps(news, indent=2))
