import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

# Function to generate summary
def summarize_text(text, max_sentences=2):
    if not text:
        return "No content to summarize."

    # Tokenize sentences
    sentences = sent_tokenize(text)

    # Tokenize words
    words = word_tokenize(text.lower())

    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    words = [word for word in words if word.isalnum() and word not in stop_words]

    # Frequency distribution
    freq = nltk.FreqDist(words)

    # Score each sentence
    sentence_scores = {}
    for sent in sentences:
        for word in word_tokenize(sent.lower()):
            if word in freq:
                if sent not in sentence_scores:
                    sentence_scores[sent] = freq[word]
                else:
                    sentence_scores[sent] += freq[word]

    # Pick top sentences
    summary_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:max_sentences]

    return " ".join(summary_sentences)



