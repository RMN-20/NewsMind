from flask import Flask, render_template, request
from app.news_fetcher import fetch_headlines
from app.summarizer import summarize_text
from app.sentiment import analyze_sentiment
from nrclex import NRCLex
import os
import re
import random
import plotly.express as px
import plotly.graph_objs as go
import plotly
import json
from wordcloud import WordCloud

app = Flask(__name__)

# Store results in memory (simple way)
latest_analysis = {}

@app.route("/", methods=["GET", "POST"])
def home():
    global latest_analysis

    topic = request.args.get("topic", "mental health")

    # Fetch news
    articles = fetch_headlines(topic, language="en", page_size=10)
    results = []

    sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
    summaries = []

    for idx, article in enumerate(articles):
        title = article["title"]
        url = article["url"]
        content = article.get("content") or article.get("description") or title

        # --- 🧹 Clean unwanted HTML and trailing numbers ---
        content = re.sub(r"<.*?>", "", content)  # remove HTML tags
        content = re.sub(r"\[\+\d+\s*chars\]", "", content)  # remove [+2555 chars]
        content = re.sub(r"\d{3,5}$", "", content.strip())  # remove stray numbers at end
        content = content.strip()

        # --- Summarize and analyze ---
        summary = summarize_text(content, max_sentences=2)
        sentiment = analyze_sentiment(summary)
        sentiment_counts[sentiment] += 1
        summaries.append(summary)

        results.append({
            "id": idx + 1,
            "title": title,
            "url": url,
            "summary": summary,
            "sentiment": sentiment
        })

    # Save latest analysis for Insights page
    latest_analysis = {
        "topic": topic,
        "articles": results,
        "counts": sentiment_counts,
        "summaries": summaries
    }

    return render_template("index.html", articles=results, topic=topic)


@app.route("/insights")
def insights():
    global latest_analysis

    if not latest_analysis:
        return "<h3>No analysis available. Please fetch some news first.</h3>"

    topic = latest_analysis["topic"]
    counts = latest_analysis["counts"]
    articles = latest_analysis["articles"]
    summaries = latest_analysis["summaries"]

    # --- Interactive Pie Chart ---
    pie_fig = px.pie(
        names=list(counts.keys()),
        values=list(counts.values()),
        color=list(counts.keys()),
        color_discrete_map={"Positive": "green", "Negative": "red", "Neutral": "gray"},
        title=f"Sentiment Distribution - {topic.title()}"
    )
    pie_json = json.dumps({"data": pie_fig["data"], "layout": pie_fig["layout"]}, cls=plotly.utils.PlotlyJSONEncoder)

    # --- Interactive Bar Chart ---
    bar_fig = px.bar(
        x=list(counts.keys()),
        y=list(counts.values()),
        color=list(counts.keys()),
        color_discrete_map={"Positive": "green", "Negative": "red", "Neutral": "gray"},
        title=f"Sentiment Count - {topic.title()}"
    )
    bar_json = json.dumps({"data": bar_fig["data"], "layout": bar_fig["layout"]}, cls=plotly.utils.PlotlyJSONEncoder)

    # --- Trend Line ---
    sentiment_map = {"Positive": 1, "Neutral": 0, "Negative": -1}
    trend_fig = go.Figure()
    trend_fig.add_trace(go.Scatter(
        x=[a["id"] for a in articles],
        y=[sentiment_map[a["sentiment"]] for a in articles],
        mode="lines+markers",
        line=dict(color="blue"),
        marker=dict(size=10),
        name="Sentiment Trend"
    ))
    trend_fig.update_layout(
        title="Sentiment Trend Over Articles",
        xaxis_title="Article Order",
        yaxis_title="Sentiment Score (-1 to 1)"
    )
    trend_json = json.dumps({"data": trend_fig["data"], "layout": trend_fig["layout"]}, cls=plotly.utils.PlotlyJSONEncoder)

    # --- Word Cloud ---
    text = " ".join(summaries)
    wc = WordCloud(width=800, height=400, background_color="white").generate(text)
    wc_path = os.path.join("static", "wordcloud.png")
    wc.to_file(wc_path)

    # --- Emotion Detection using NRCLex ---
    all_text = " ".join(summaries)
    emotion_obj = NRCLex(all_text)
    emotion_scores = emotion_obj.raw_emotion_scores

    # Ensure all 8 emotion categories exist
    emotion_categories = ["joy", "sadness", "fear", "anger", "trust", "disgust", "anticipation", "surprise"]
    emotion_values = [emotion_scores.get(e, 0) for e in emotion_categories]

    # --- Radar Chart ---
    radar_fig = go.Figure()
    radar_fig.add_trace(go.Scatterpolar(
        r=emotion_values + [emotion_values[0]],  # close the loop
        theta=emotion_categories + [emotion_categories[0]],
        fill='toself',
        name="Emotions",
        line=dict(color="purple")
    ))
    radar_fig.update_layout(
        title="Emotion Distribution (NRCLex)",
        polar=dict(radialaxis=dict(visible=True, range=[0, max(emotion_values) + 1 if emotion_values else 1])),
        showlegend=False
    )
    radar_json = json.dumps({"data": radar_fig["data"], "layout": radar_fig["layout"]}, cls=plotly.utils.PlotlyJSONEncoder)

    # --- Awareness Insights ---
    suggestions = []
    dominant_emotion = max(emotion_scores, key=emotion_scores.get) if emotion_scores else "neutral"

    if counts["Negative"] > counts["Positive"]:
        if dominant_emotion in ["fear", "sadness", "anger"]:
            suggestions.append("🕊 It seems the recent news carries heavy emotions like fear or sadness. Take short breaks from screens.")
        elif dominant_emotion == "disgust":
            suggestions.append("⚠️ Some stories may trigger discomfort. Consider journaling or talking about your thoughts.")
        else:
            suggestions.append("☁️ A wave of negativity can weigh you down. Try spending time outdoors or doing a quick mindfulness exercise.")
    elif counts["Positive"] > counts["Negative"]:
        if dominant_emotion == "joy":
            suggestions.append("🌞 A lot of joyful energy! Celebrate small wins and spread that positivity to others today.")
        elif dominant_emotion == "trust":
            suggestions.append("💬 The tone feels uplifting and trustworthy — a great time to reflect or share something kind online.")
        else:
            suggestions.append("✨ The news seems mostly positive. Stay engaged but balanced with relaxing breaks.")
    else:
        suggestions.append("📊 The tone is mostly neutral. Try exploring diverse perspectives to stay informed without feeling overwhelmed.")

    # --- Motivational Prompts ---
    prompts = [
        "🧘 Take 5 minutes to do mindful breathing — inhale calm, exhale tension.",
        "🎧 Listen to your favorite song or nature sounds for a quick mental reset.",
        "📖 Read something inspiring — a poem, quote, or short story.",
        "☕ Hydrate and stretch — small actions make a big difference.",
        "💬 Talk to a friend or family member about something good that happened today."
    ]

    quotes = [
        "💭 'Peace comes from within. Do not seek it without.' – Buddha",
        "🌿 'You can’t stop the waves, but you can learn to surf.' – Jon Kabat-Zinn",
        "🌅 'In the middle of difficulty lies opportunity.' – Albert Einstein",
        "🕊 'Take rest; a field that has rested gives a bountiful crop.' – Ovid",
        "☀️ 'Almost everything will work again if you unplug it for a few minutes, including you.' – Anne Lamott"
    ]

    suggestions.append(random.choice(prompts))
    suggestions.append(random.choice(quotes))

    return render_template(
        "insights.html",
        topic=topic,
        pie_json=pie_json,
        bar_json=bar_json,
        trend_json=trend_json,
        radar_json=radar_json,
        wordcloud="wordcloud.png",
        suggestions=suggestions
    )


if __name__ == "__main__":
    app.run(debug=True)
