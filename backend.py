import re
from flask import Flask, jsonify, request

app = Flask(__name__, static_folder='.', static_url_path='')

sentiment_map = {
    'positive': [
        'good', 'great', 'excellent', 'love', 'loved', 'amazing', 'fantastic', 'perfect', 'happy', 'recommend',
        'easy', 'fast', 'friendly', 'comfortable', 'enjoyed', 'best', 'beautiful', 'helpful', 'superb', 'attentive', 'responsive', 'speedy', 'quick', 'prompt', 'satisfied', 'awesome'
    ],
    'negative': [
        'bad', 'poor', 'terrible', 'awful', 'hate', 'disappoint', 'slow', 'expensive', 'problem',
        'issue', 'worst', 'broken', 'late', 'rude', 'hard', 'uncomfortable', 'difficult'
    ]
}

stopwords = {
    'and', 'the', 'a', 'an', 'to', 'for', 'of', 'in', 'on', 'with', 'that', 'this', 'was', 'is', 'it',
    'they', 'their', 'from', 'as', 'but', 'at', 'by', 'be', 'are', 'were', 'have', 'has', 'had', 'not',
    'or', 'so', 'if', 'we', 'you', 'your', 'our', 'can', 'will', 'its'
}

categories = {
    'product': ['quality', 'product', 'material', 'durable', 'fit', 'size'],
    'delivery': ['delivery', 'shipping', 'late', 'packaging', 'arrived'],
    'service': ['service', 'support', 'helpful', 'customer', 'staff', 'agent', 'team']
}


def clean_text(text):
    cleaned = text.lower()
    cleaned = re.sub(r'\d+', '', cleaned)
    cleaned = re.sub(r'[^a-z\s]+', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


def get_keywords(words, limit=8):
    freq = {}
    for word in words:
        if len(word) < 3 or word in stopwords:
            continue
        freq[word] = freq.get(word, 0) + 1
    return [word for word, _ in sorted(freq.items(), key=lambda item: item[1], reverse=True)[:limit]]


def classify_review(words):
    scores = {key: 0 for key in categories}
    for word in words:
        for key, terms in categories.items():
            if word in terms:
                scores[key] += 1
    primary = max(scores.items(), key=lambda item: item[1])
    return primary[0] if primary[1] > 0 else 'general feedback'


def analyze_sentiment(words):
    positive = sum(1 for word in words if any(term in word for term in sentiment_map['positive']))
    negative = sum(1 for word in words if any(term in word for term in sentiment_map['negative']))
    total_sentiment_words = positive + negative
    score = round(((positive - negative) / total_sentiment_words) * 100) if total_sentiment_words else 0
    score = max(-100, min(100, score))
    label = 'Positive' if positive > negative else 'Negative' if negative > positive else 'Neutral'
    return {
        'positive': positive,
        'negative': negative,
        'score': score,
        'label': label
    }


def suggest_rating(score):
    if score >= 45:
        return '5 stars'
    if score >= 15:
        return '4 stars'
    if score >= -5:
        return '3 stars'
    if score >= -30:
        return '2 stars'
    return '1 star'


def build_notes(words, sentiment):
    notes = [
        f'Detected {len(words)} words in reviews.',
        f'Positive terms: {sentiment["positive"]}, negative terms: {sentiment["negative"]}.',
    ]
    if sentiment['score'] >= 45:
        notes.append('The review sentiment is strongly positive.')
    elif sentiment['score'] <= -45:
        notes.append('The review sentiment is strongly negative and may require immediate attention.')
    else:
        notes.append('The sentiment is mixed; consider deeper analysis for nuance.')
    return notes


def analyze_review_text(raw):
    cleaned = ''.join(ch.lower() if ch.isalpha() or ch.isspace() else ' ' for ch in raw)
    words = [word for word in cleaned.split() if word]
    sentiment = analyze_sentiment(words)
    return {
        'sentimentScore': sentiment['score'],
        'sentimentLabel': sentiment['label'],
        'ratingSuggestion': suggest_rating(sentiment['score']),
        'categoryLabel': classify_review(words),
        'keywords': get_keywords(words),
        'notes': build_notes(words, sentiment)
    }


@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.get_json(silent=True)
    if not data or 'text' not in data or not isinstance(data['text'], str):
        return jsonify({'error': 'Missing review text.'}), 400
    return jsonify(analyze_review_text(data['text']))


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)


@app.route('/config.json')
def config():
    """Return runtime config (useful when served through ngrok or different host).
    The `apiBase` lets the frontend construct an absolute API URL matching the
    current request host (works both for localhost and public ngrok URL).
    """
    base = request.host_url.rstrip('/')
    return jsonify({'apiBase': base})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
