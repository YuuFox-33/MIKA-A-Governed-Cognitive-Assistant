import nltk
import spacy
from nltk.corpus import wordnet as wn
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from typing import Tuple, Optional, Dict

# Download necessary resources (run once)
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

nlp = spacy.load("en_core_web_sm")

class TextUnderstandingLayer:
    def __init__(self, config):
        self.config = config
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Example training set for intent classification
        self.intent_examples = {
            "greeting": ["hello", "hi there", "hey", "hiya", "yo"],
            "gratitude": ["thank you", "thanks", "i appreciate you", "good job"],
            "goodbye": ["bye", "see you", "goodbye", "exit", "shut down"],
            "emotion_check": ["how are you", "how do you feel", "are you okay"],
            "conversation": ["just chatting", "talk to me", "let’s talk", "can we talk"]
        }

        self.vectorizer = CountVectorizer()
        self.classifier = MultinomialNB()
        self._train_intent_classifier()

    def _train_intent_classifier(self):
        X = []
        y = []
        for intent, phrases in self.intent_examples.items():
            X.extend(phrases)
            y.extend([intent] * len(phrases))
        X_vec = self.vectorizer.fit_transform(X)
        self.classifier.fit(X_vec, y)

    def analyze(self, text: str) -> Tuple[str, Dict]:
        """
        Analyze input text for intent, sentiment, NER, and semantic similarity.
        """
        if not text or not isinstance(text, str):
            return "unknown", {}

        cleaned = text.lower().strip()

        # Intent Classification
        X_input = self.vectorizer.transform([cleaned])
        predicted_intent = self.classifier.predict(X_input)[0]
        intent_prob = max(self.classifier.predict_proba(X_input)[0])

        # Sentiment Analysis
        sentiment = self.sentiment_analyzer.polarity_scores(cleaned)

        # Named Entity Recognition (NER)
        doc = nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]

        # Semantic similarity to known intent examples
        similarity_scores = {}
        for intent, examples in self.intent_examples.items():
            example_embeddings = self.embedding_model.encode(examples, convert_to_tensor=True)
            input_embedding = self.embedding_model.encode(cleaned, convert_to_tensor=True)
            max_sim = max(util.cos_sim(input_embedding, example_embeddings)[0])
            similarity_scores[intent] = float(max_sim)

        # Best semantic match if classifier is unsure
        if intent_prob < 0.6:
            predicted_intent = max(similarity_scores, key=similarity_scores.get)

        return predicted_intent, {
            "text": text,
            "confidence": intent_prob,
            "sentiment": sentiment,
            "entities": entities,
            "semantic_similarity": similarity_scores
        }
