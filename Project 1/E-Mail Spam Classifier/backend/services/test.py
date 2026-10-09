import joblib
import os
import sys

base_dir = os.path.dirname(os.path.dirname(__file__))
model_path = os.path.join(base_dir, 'model', 'spam_classifier.pkl')
vectorizer_path = os.path.join(base_dir, 'model', 'tfidf_vectorizer.pkl')

model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)

msg = ["Congratulations! You have won a FREE cash prize."]
feat = vectorizer.transform(msg)
pred = model.predict(feat)
print(pred)
