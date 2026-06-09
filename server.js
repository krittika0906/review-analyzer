const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname)));

const sentimentMap = {
  positive: [
    'good', 'great', 'excellent', 'love', 'loved', 'amazing', 'fantastic', 'perfect', 'happy', 'recommend',
    'easy', 'fast', 'friendly', 'comfortable', 'enjoyed', 'best', 'beautiful', 'helpful', 'superb', 'attentive', 'responsive', 'speedy', 'quick', 'prompt', 'satisfied', 'awesome'
  ],
  negative: [
    'bad', 'poor', 'terrible', 'awful', 'hate', 'disappoint', 'slow', 'expensive', 'problem',
    'issue', 'worst', 'broken', 'late', 'rude', 'hard', 'uncomfortable', 'difficult'
  ]
};

const stopwords = new Set([
  'and','the','a','an','to','for','of','in','on','with','that','this','was','is','it','they','their','from','as','but',
  'at','by','be','are','were','have','has','had','not','or','so','if','we','you','your','our','can','will','its'
]);

const categories = {
  product: ['quality', 'product', 'material', 'durable', 'fit', 'size'],
  delivery: ['delivery', 'shipping', 'late', 'packaging', 'arrived'],
  service: ['service', 'support', 'helpful', 'customer', 'staff', 'agent', 'team']
};

function cleanText(text) {
  return text
    .toLowerCase()
    .replace(/[\d]/g, '')
    .replace(/[^a-z\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function getKeywords(words, limit = 8) {
  const freq = new Map();
  words.forEach((word) => {
    if (word.length < 3 || stopwords.has(word)) return;
    freq.set(word, (freq.get(word) || 0) + 1);
  });
  return Array.from(freq.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([word]) => word);
}

function classifyReview(words) {
  const scores = { product: 0, delivery: 0, service: 0 };
  words.forEach((word) => {
    Object.entries(categories).forEach(([key, terms]) => {
      if (terms.includes(word)) scores[key] += 1;
    });
  });

  const primary = Object.entries(scores).sort((a, b) => b[1] - a[1])[0];
  return primary[1] > 0 ? primary[0] : 'general feedback';
}

function analyzeSentiment(words) {
  let positive = 0;
  let negative = 0;

  words.forEach((word) => {
    if (sentimentMap.positive.some((term) => word.includes(term))) positive += 1;
    if (sentimentMap.negative.some((term) => word.includes(term))) negative += 1;
  });

  const score = words.length ? ((positive - negative) / words.length) * 100 : 0;
  return {
    positive,
    negative,
    score: Math.max(-100, Math.min(100, Math.round(score))),
    label: score > 12 ? 'Positive' : score < -12 ? 'Negative' : 'Neutral'
  };
}

function suggestRating(score) {
  if (score >= 45) return '5 stars';
  if (score >= 15) return '4 stars';
  if (score >= -5) return '3 stars';
  if (score >= -30) return '2 stars';
  return '1 star';
}

function buildNotes(words, sentiment) {
  const notes = [
    `Detected ${words.length} words in reviews.`,
    `Positive terms: ${sentiment.positive}, negative terms: ${sentiment.negative}.`,
  ];

  if (sentiment.score >= 45) {
    notes.push('The review sentiment is strongly positive.');
  } else if (sentiment.score <= -45) {
    notes.push('The review sentiment is strongly negative and may require immediate attention.');
  } else {
    notes.push('The sentiment is mixed; consider deeper analysis for nuance.');
  }

  return notes;
}

function analyzeReviewText(raw) {
  const cleaned = cleanText(raw);
  const words = cleaned.split(' ').filter(Boolean);
  const sentiment = analyzeSentiment(words);
  const keywords = getKeywords(words);
  const category = classifyReview(words);
  const rating = suggestRating(sentiment.score);

  return {
    sentimentScore: sentiment.score,
    sentimentLabel: sentiment.label,
    ratingSuggestion: rating,
    categoryLabel: category,
    keywords,
    notes: buildNotes(words, sentiment)
  };
}

app.post('/api/analyze', (req, res) => {
  const { text } = req.body;
  if (typeof text !== 'string' || !text.trim()) {
    return res.status(400).json({ error: 'Missing review text.' });
  }
  res.json(analyzeReviewText(text));
});

app.get('/config.json', (req, res) => {
  const base = `${req.protocol}://${req.get('host')}`.replace(/\/$/, '');
  res.json({ apiBase: base });
});

app.listen(PORT, () => {
  console.log(`Review Analyzer backend running at http://localhost:${PORT}`);
});
