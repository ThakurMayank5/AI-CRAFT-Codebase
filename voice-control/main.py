import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load embedding model
model = SentenceTransformer("all-MiniLM-L12-v2")

# Load intents
with open("intents.json", "r") as f:
    INTENTS = json.load(f)

# Known appliances (can expand later)
APPLIANCES = ["light"]   # later: ["light", "fan", "motor"]

def generate_intent_sentences():
    sentences = []
    labels = []

    for intent, patterns in INTENTS.items():
        for appliance in APPLIANCES:
            for p in patterns:
                sentence = p.replace("{appliance}", appliance)
                sentences.append(sentence)
                labels.append(intent)

    return sentences, labels


# Precompute embeddings
intent_sentences, intent_labels = generate_intent_sentences()

print(intent_sentences)

intent_embeddings = model.encode(intent_sentences)

def predict_intent(text):
    text_embedding = model.encode([text])
    similarities = cosine_similarity(text_embedding, intent_embeddings)[0]

    best_idx = np.argmax(similarities)
    best_intent = intent_labels[best_idx]
    confidence = float(similarities[best_idx])

    return best_intent, confidence


def extract_appliance(text):
    text = text.lower()
    for appliance in APPLIANCES:
        if appliance in text:
            return appliance
    return None


# -------- TEST --------
if __name__ == "__main__":
    user_text = "please turn on the bedroom fan"

    intent, score = predict_intent(user_text)
    appliance = extract_appliance(user_text)

    print("Intent:", intent)
    print("Appliance:", appliance)
    print("Confidence:", round(score, 3))
