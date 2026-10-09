import React from 'react';
import { ArrowDown } from 'lucide-react';

export default function HowItWorks() {
  const steps = [
    {
      title: '1. Email Input',
      desc: 'The system receives a new message from the connected Gmail account or custom input.',
      bg: 'bg-gray-100',
      textColor: 'text-gray-800'
    },
    {
      title: '2. Text Cleaning',
      desc: 'Converts the message into a normalized text format (lowercase, removing punctuation) as used during training.',
      bg: 'bg-blue-50',
      textColor: 'text-blue-800'
    },
    {
      title: '3. TF-IDF Transformation',
      desc: 'Converts text into numerical features based on word and phrase (n-gram) importance using the saved vectorizer.',
      bg: 'bg-indigo-50',
      textColor: 'text-indigo-800'
    },
    {
      title: '4. Linear SVM Inference',
      desc: 'The frozen ML model uses its learned decision boundary to classify the numerical features.',
      bg: 'bg-purple-50',
      textColor: 'text-purple-800'
    }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">How It Works</h2>
        <p className="text-gray-500">The pipeline from raw text to prediction</p>
      </div>

      <div className="max-w-2xl mx-auto py-8">
        {steps.map((step, idx) => (
          <React.Fragment key={idx}>
            <div className={`${step.bg} p-6 rounded-xl border border-black/5 text-center shadow-sm relative`}>
              <h3 className={`font-bold text-lg mb-2 ${step.textColor}`}>{step.title}</h3>
              <p className="text-gray-600 text-sm">{step.desc}</p>
            </div>
            
            {idx < steps.length - 1 && (
              <div className="flex justify-center py-4">
                <ArrowDown className="text-gray-300 w-8 h-8" />
              </div>
            )}
          </React.Fragment>
        ))}

        <div className="flex justify-center py-4">
          <ArrowDown className="text-gray-300 w-8 h-8" />
        </div>

        <div className="flex gap-4">
          <div className="flex-1 bg-green-50 border-2 border-green-200 p-4 rounded-xl text-center shadow-sm">
            <div className="font-black text-xl text-green-700 tracking-wider">HAM</div>
          </div>
          <div className="flex-1 bg-red-50 border-2 border-red-200 p-4 rounded-xl text-center shadow-sm">
            <div className="font-black text-xl text-red-700 tracking-wider">SPAM</div>
          </div>
        </div>
      </div>
    </div>
  );
}
