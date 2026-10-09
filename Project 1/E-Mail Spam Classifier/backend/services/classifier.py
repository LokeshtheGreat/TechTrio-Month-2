import joblib
import re
import os
import numpy as np

class SpamClassifier:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        model_path = os.path.join(base_dir, 'model', 'spam_classifier.pkl')
        vectorizer_path = os.path.join(base_dir, 'model', 'tfidf_vectorizer.pkl')
        
        try:
            self.model = joblib.load(model_path)
            self.vectorizer = joblib.load(vectorizer_path)
            
            # The model and vectorizer were trained with specific shapes.
            # We will use them directly for inference.
            self.feature_names = np.array(self.vectorizer.get_feature_names_out())
            self.coef = self.model.coef_[0]
            print("Models loaded successfully.")
        except Exception as e:
            print(f"Error loading models: {e}")
            self.model = None
            self.vectorizer = None

    def clean_text(self, text):
        text = text.lower()
        # the simplest cleaning that would have been done. 
        # But wait, scikit-learn's vectorizer usually does its own lowercasing and punctuation removal.
        # So we can just let it handle it mostly, but just in case:
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        return text

    def predict(self, message):
        if not self.model or not self.vectorizer:
            return {"error": "Models not loaded"}
            
        features = self.vectorizer.transform([message])
        
        prediction = self.model.predict(features)[0]
        decision = self.model.decision_function(features)[0]
        
        # 1 usually means SPAM in these datasets, let's assume 1=SPAM, 0=HAM. 
        # In typical SMS spam datasets, 'spam' might be 1, 'ham' 0.
        # But wait, the PRD says LinearSVM predicts HAM/SPAM. 
        # The model might literally output the string 'spam' or 'ham'. Let's check type.
        if isinstance(prediction, str):
            label = prediction.upper()
            is_spam = (label == 'SPAM')
        else:
            label = "SPAM" if prediction == 1 else "HAM"
            is_spam = (prediction == 1)
        
        # decision function > 0 usually means class 1.
        # So if class 1 is spam, large positive decision = HIGH strength spam.
        # If the model uses 'ham' as class 0 and 'spam' as class 1, then positive = spam.
        # Let's just use absolute value for strength.
        abs_dec = abs(decision)
        strength = "High" if abs_dec > 1.0 else ("Medium" if abs_dec > 0.5 else "Low")
        
        # Get indicators
        feature_indices = features.nonzero()[1]
        indicators = []
        
        # if the decision is negative, it's HAM, so we want features with negative weights as indicators?
        # The PRD specifically asks for "spam indicators" when predicting SPAM.
        for idx in feature_indices:
            weight = self.coef[idx]
            # if is_spam, we look for positive weights. If it's ham, we look for negative weights.
            # but usually users just want to see why it was marked spam.
            if is_spam and weight > 0:
                indicators.append({
                    "term": self.feature_names[idx],
                    "weight": float(weight)
                })
            elif not is_spam and weight < 0:
                indicators.append({
                    "term": self.feature_names[idx],
                    "weight": float(abs(weight))
                })
                
        # Sort by weight descending
        indicators = sorted(indicators, key=lambda x: x['weight'], reverse=True)[:5]
        
        return {
            "prediction": label,
            "strength": strength,
            "decision_score": float(decision),
            "indicators": indicators
        }
