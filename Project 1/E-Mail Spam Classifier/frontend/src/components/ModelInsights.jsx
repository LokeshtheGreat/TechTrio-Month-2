import React from 'react';

export default function ModelInsights() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Model Insights</h2>
        <p className="text-gray-500">Details about the underlying Machine Learning system</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-4">
          <h3 className="text-lg font-bold text-gray-900 border-b pb-2">Algorithm</h3>
          <div>
            <div className="text-xl font-semibold text-blue-600">Linear Support Vector Classifier</div>
            <p className="text-gray-600 mt-2 text-sm">
              Chosen for its excellent performance in high-dimensional text classification tasks. 
              It creates a hyperplane that best separates spam and ham messages.
            </p>
          </div>
          
          <div className="pt-4">
            <h4 className="font-semibold text-gray-700 mb-2">Hyperparameters</h4>
            <div className="bg-gray-50 p-4 rounded-lg font-mono text-sm text-gray-800">
              <div>C = 0.1</div>
              <div>class_weight = "balanced"</div>
              <div>loss = "squared_hinge"</div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-4">
          <h3 className="text-lg font-bold text-gray-900 border-b pb-2">Feature Extraction</h3>
          <div>
            <div className="text-xl font-semibold text-purple-600">TF-IDF Vectorizer</div>
            <p className="text-gray-600 mt-2 text-sm">
              Term Frequency - Inverse Document Frequency. Converts text into numerical features based on word importance across the dataset.
            </p>
          </div>
          
          <div className="pt-4">
            <h4 className="font-semibold text-gray-700 mb-2">Parameters</h4>
            <div className="bg-gray-50 p-4 rounded-lg font-mono text-sm text-gray-800">
              <div>ngram_range = (1, 3)</div>
              <div>lowercase = True</div>
              <div>stop_words = None</div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm mt-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4 border-b pb-2">Hyperparameter Analysis</h3>
        <p className="text-gray-600 text-sm mb-6">
          During development, different C-values were tested. C=0.1 was chosen to provide stronger regularization, 
          reducing false positives (classifying ham as spam) while maintaining high overall accuracy.
        </p>
        
        <div className="flex gap-4 mb-4">
          <div className="flex-1 bg-blue-50 p-3 rounded text-center">
            <div className="font-bold text-blue-800">C = 0.1</div>
            <div className="text-xs text-blue-600">Deployed (Best Balance)</div>
          </div>
          <div className="flex-1 bg-gray-50 p-3 rounded text-center">
            <div className="font-bold text-gray-700">C = 0.5</div>
          </div>
          <div className="flex-1 bg-gray-50 p-3 rounded text-center">
            <div className="font-bold text-gray-700">C = 1.0</div>
          </div>
          <div className="flex-1 bg-gray-50 p-3 rounded text-center">
            <div className="font-bold text-gray-700">C = 2.0</div>
          </div>
        </div>
      </div>
    </div>
  );
}
