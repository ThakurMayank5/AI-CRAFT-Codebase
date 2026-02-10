import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import whisper

whisper_model = whisper.load_model("base")

# Load embedding model
model = SentenceTransformer("all-MiniLM-L12-v2")

# Load intent templates
with open("intents.json", "r") as f:
    INTENTS = json.load(f)


def generate_intent_sentences(appliance):
    """
    Generate intent sentences by replacing {appliance}
    dynamically at runtime.
    """
    sentences = []
    labels = []

    for intent, patterns in INTENTS.items():
        for p in patterns:
            sentence = p.replace("{appliance}", appliance)
            sentences.append(sentence)
            labels.append(intent)

    return sentences, labels


def predict_intent(text, appliance):
    """
    Predict intent for a given text and appliance name.
    """
    intent_sentences, intent_labels = generate_intent_sentences(appliance)

    intent_embeddings = model.encode(intent_sentences)
    text_embedding = model.encode([text])

    similarities = cosine_similarity(text_embedding, intent_embeddings)[0]

    best_idx = np.argmax(similarities)
    best_intent = intent_labels[best_idx]
    confidence = float(similarities[best_idx])

    return best_intent, confidence, intent_sentences, similarities



# -------- TEST --------
if __name__ == "__main__":



    result = whisper_model.transcribe("sample.m4a", language="en")

    text=result["text"]
    # text="Turn off the fan"

    print("Transcript:")
    print(text)




    user_text = text

    prediction=0
    appliance_predicted = None
    intent_predicted = None


    for appliance_name in ["lights", "fan", "ac"]:
        intent, score, sentences, sims = predict_intent(user_text, appliance_name)

        if prediction==0 or score>prediction:
            intent_predicted=intent
            prediction=score
            appliance_predicted=appliance_name


    print(prediction )
    print(appliance_predicted)
    print(intent_predicted)

    # appliance_name = "fan"   # ← dynamic input

    # intent, score, sentences, sims = predict_intent(user_text, appliance_name)

    # print("Intent:", intent)
    # print("Appliance:", appliance_name)
    # print("Confidence:", round(score, 3))

    # print("\nSimilarity breakdown:")
    # for s, v in zip(sentences, sims):
    #     print(f"{v:.3f}  |  {s}")
    # appliance_name = "lights"   # ← dynamic input

    # intent, score, sentences, sims = predict_intent(user_text, appliance_name)

    # print("Intent:", intent)
    # print("Appliance:", appliance_name)
    # print("Confidence:", round(score, 3))

    # print("\nSimilarity breakdown:")
    # for s, v in zip(sentences, sims):
    #     print(f"{v:.3f}  |  {s}")
