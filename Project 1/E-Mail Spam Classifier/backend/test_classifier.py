from services.classifier import SpamClassifier

classifier = SpamClassifier()

tests = [
    "Please immediately send your documents",
    "Here is your free ticket to the event.",
    "URGENT: Your account has been compromised. Please reset your password.",
    "Hey, do you want to grab lunch today? I have a free hour at 1pm.",
    "This is an official transactional email regarding your recent purchase."
]

for text in tests:
    res = classifier.predict(text)
    print(f"TEXT: {text}")
    print(f"PREDICTION: {res['prediction']} (Strength: {res['strength']})")
    
    # We want to see the model-derived feature weights and decision scores
    # Let's dig into the model itself
    transformed = classifier.vectorizer.transform([classifier.clean_text(text)])
    score = classifier.model.decision_function(transformed)[0]
    print(f"DECISION SCORE (raw distance to hyperplane): {score}")
    
    print("TOP INDICATORS:")
    for ind in res['indicators'][:5]:
        print(f"  - {ind['term']}: {ind['weight']}")
    
    print("-" * 50)
