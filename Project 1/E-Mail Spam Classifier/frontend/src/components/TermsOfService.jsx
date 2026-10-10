import React from 'react';
import { Shield, ArrowLeft, FileText, CheckCircle2, AlertCircle, AlertTriangle, Scale, Cpu, UserCheck, RefreshCw, Mail, Ban, Lock, ExternalLink } from 'lucide-react';

export default function TermsOfService({ onNavigate }) {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-800">
      {/* Top Header Navigation */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigate('app')}
              className="flex items-center gap-2 text-blue-600 font-bold text-lg hover:opacity-90 transition-opacity"
              title="Return to Email Spam Shield"
            >
              <Shield className="w-6 h-6 text-blue-600 flex-shrink-0" />
              <span>Spam Shield</span>
            </button>
            <span className="text-gray-300">/</span>
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
              Legal
            </span>
          </div>

          <div className="flex items-center gap-3">
            <a
              href="/privacy-policy"
              onClick={(e) => {
                if (!e.ctrlKey && !e.metaKey && !e.shiftKey && e.button === 0) {
                  e.preventDefault();
                  onNavigate('privacy-policy');
                }
              }}
              className="text-xs font-medium text-gray-600 hover:text-blue-600 transition-colors px-2 py-1"
            >
              Privacy Policy
            </a>
            <a
              href="/"
              onClick={(e) => {
                if (!e.ctrlKey && !e.metaKey && !e.shiftKey && e.button === 0) {
                  e.preventDefault();
                  onNavigate('app');
                }
              }}
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg transition-colors border border-blue-200/60"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to App</span>
            </a>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
        {/* Document Header Card */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 sm:p-10 shadow-sm mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 text-blue-700 border border-blue-100 rounded-full text-xs font-semibold mb-4">
            <Scale className="w-3.5 h-3.5" />
            <span>Public Legal Document</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight mb-3">
            Terms of Service
          </h1>
          <p className="text-sm text-gray-500 mb-6">
            <strong>Effective Date:</strong> October 10, 2026 &nbsp;|&nbsp; <strong>Last Updated:</strong> October 10, 2026
          </p>
          <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
            Welcome to <strong>Email Spam Shield</strong>. These Terms of Service (&ldquo;Terms&rdquo;) govern your access to and use of our web application, tools, and services hosted at{' '}
            <a href="https://e-mail-spam-shield.vercel.app/" className="text-blue-600 hover:underline font-medium">
              https://e-mail-spam-shield.vercel.app/
            </a>{' '}
            (the &ldquo;Service&rdquo;), developed and operated by Lokeshwar L (&ldquo;we&rdquo;, &ldquo;us&rdquo;, or &ldquo;our&rdquo;).
          </p>

          <div className="mt-6 p-4 bg-amber-50/80 border border-amber-200/80 rounded-xl text-xs sm:text-sm text-amber-900 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold mb-1">Important Notice on Machine Learning &amp; Verification</p>
              <p className="text-amber-800 leading-relaxed">
                Email Spam Shield uses probabilistic machine learning to analyze emails for spam and phishing. Predictions are diagnostic suggestions and may include false positives or false negatives. You remain solely responsible for reviewing and verifying all important, sensitive, or critical communications.
              </p>
            </div>
          </div>
        </div>

        {/* Detailed Sections */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 sm:p-10 shadow-sm space-y-10 text-sm sm:text-base leading-relaxed text-gray-700">
          
          {/* Section 1 */}
          <section id="acceptance" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">1</span>
              Acceptance of Terms
            </h2>
            <p>
              By accessing the website, registering an account, or connecting your Google Gmail account, you signify that you have read, understood, and agreed to be legally bound by these Terms of Service and our{' '}
              <button onClick={() => onNavigate('privacy-policy')} className="text-blue-600 hover:underline font-medium inline">
                Privacy Policy
              </button>
              .
            </p>
            <p>
              If you do not agree to these Terms, you must not access or use Email Spam Shield. If you are using the Service on behalf of an organization, you represent and warrant that you have authority to bind that entity to these Terms.
            </p>
          </section>

          <hr className="border-gray-100" />

          {/* Section 2 */}
          <section id="service-description" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">2</span>
              Description of the Service
            </h2>
            <p>
              Email Spam Shield is a web-based email security dashboard and spam classification tool. The platform provides:
            </p>
            <ul className="list-disc pl-6 space-y-1.5 text-gray-600">
              <li>
                <strong>Automated Ingestion:</strong> Secure retrieval of recent message metadata and text from connected Gmail mailboxes via Google APIs.
              </li>
              <li>
                <strong>Machine Learning Classification:</strong> Classification of email text into <em>SPAM</em> or <em>HAM</em> (legitimate) categories using internal machine learning models.
              </li>
              <li>
                <strong>Diagnostic Indicators:</strong> Extraction and visualization of influential tokens and keywords that drove the model&rsquo;s decision.
              </li>
              <li>
                <strong>Live Monitoring &amp; Analytics:</strong> A real-time dashboard displaying recent message verdicts, confidence indicators, and overall inbox statistics.
              </li>
            </ul>
            <p className="text-xs text-gray-500">
              Note: Email Spam Shield acts exclusively as an analytical observation tool. It does not delete, quarantine, or alter messages inside your Gmail account.
            </p>
          </section>

          <hr className="border-gray-100" />

          {/* Section 3 */}
          <section id="user-accounts" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">3</span>
              User Accounts &amp; Registration
            </h2>
            <p>
              To connect your Gmail account and access live monitoring, you must register an account authenticated through Supabase. You agree to:
            </p>
            <ul className="list-disc pl-6 space-y-1.5 text-gray-600">
              <li>Provide accurate, current, and complete registration information.</li>
              <li>Maintain the confidentiality of your account credentials and password.</li>
              <li>Promptly notify us if you detect or suspect any unauthorized access to your account.</li>
              <li>Accept responsibility for all activities that occur under your authenticated session.</li>
            </ul>
            <p>
              You must be at least 18 years of age or the age of legal majority in your jurisdiction to use Email Spam Shield.
            </p>
          </section>

          <hr className="border-gray-100" />

          {/* Section 4 */}
          <section id="gmail-connection" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">4</span>
              Google Account Connection &amp; Read-Only Scope
            </h2>
            <p>
              When connecting your Gmail account via Google OAuth 2.0, you grant Email Spam Shield permission to access your mailbox under the specific scope:
            </p>
            <div className="p-3 bg-gray-100 font-mono text-xs text-gray-800 rounded-lg break-all">
              https://www.googleapis.com/auth/gmail.readonly
            </div>
            <div className="space-y-2 mt-2">
              <p>By connecting your Google account, you represent and warrant that:</p>
              <ul className="list-disc pl-6 space-y-1 text-gray-600">
                <li>You are the authorized account owner or have explicit permission to access and monitor the mailbox.</li>
                <li>You acknowledge that our access is <strong>strictly read-only</strong>: Email Spam Shield does not possess or request permissions to send emails, delete messages, modify drafts, manage contacts, or change mailbox settings.</li>
                <li>You may revoke this permission at any moment using the &ldquo;Disconnect&rdquo; option in the Live Monitor interface or via the Google Security permissions portal at <a href="https://myaccount.google.com/permissions" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">myaccount.google.com/permissions</a>.</li>
              </ul>
            </div>
          </section>

          <hr className="border-gray-100" />

          {/* Section 5 */}
          <section id="model-limitations" className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">5</span>
              Nature &amp; Limitations of the Spam Classifier
            </h2>
            
            <div className="p-5 bg-amber-50/60 border border-amber-200 rounded-xl space-y-3 text-sm text-amber-950">
              <div className="flex items-center gap-2 font-bold text-amber-900">
                <Cpu className="w-4 h-4 text-amber-700" />
                <span>Probabilistic Machine Learning Disclaimer</span>
              </div>
              <p>
                Email Spam Shield utilizes statistical Natural Language Processing (TF-IDF vectorization) and Support Vector Classification (scikit-learn LinearSVC). Machine learning predictions are <strong>probabilistic estimations</strong> based on pattern matching against learned training data.
              </p>
              <ul className="list-disc pl-5 space-y-1 text-amber-900">
                <li>
                  <strong>No Guarantee of Accuracy:</strong> We do not warrant or guarantee that the model will catch 100% of spam or phishing messages, or that legitimate emails will never be misidentified.
                </li>
                <li>
                  <strong>False Positives:</strong> Legitimate, important, or urgent messages may occasionally be classified as &ldquo;SPAM&rdquo;.
                </li>
                <li>
                  <strong>False Negatives:</strong> Deceptive, novel, or sophisticated spam or phishing attacks may occasionally be classified as &ldquo;HAM&rdquo;.
                </li>
                <li>
                  <strong>Advisory Role Only:</strong> Classification verdicts and confidence indicators are provided solely for informational and investigative purposes.
                </li>
              </ul>
            </div>

            <div className="space-y-2">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-blue-600" /> User Responsibility to Verify Critical Communications
              </h3>
              <p>
                You acknowledge and agree that <strong>you bear sole responsibility</strong> for verifying the safety, authenticity, and disposition of any email message before clicking links, downloading files, sharing credentials, or initiating financial transactions. Never rely exclusively on automated classification verdicts for mission-critical, legal, financial, healthcare, or security decisions.
              </p>
            </div>
          </section>

          <hr className="border-gray-100" />

          {/* Section 6 */}
          <section id="acceptable-use" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">6</span>
              Acceptable Use &amp; Prohibitions
            </h2>
            <p>You agree not to use Email Spam Shield for any unlawful, abusive, or unauthorized purpose. Specifically, you agree that you will not:</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs">
                <strong className="text-red-700 flex items-center gap-1.5 mb-1">
                  <Ban className="w-3.5 h-3.5" /> No Reverse Engineering
                </strong>
                Decompile, reverse engineer, extract weights, or clone the proprietary classification engine or APIs.
              </div>
              <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs">
                <strong className="text-red-700 flex items-center gap-1.5 mb-1">
                  <Ban className="w-3.5 h-3.5" /> No Adversarial Testing
                </strong>
                Use the service to craft adversarial spam payloads designed to bypass commercial email filtering filters.
              </div>
              <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs">
                <strong className="text-red-700 flex items-center gap-1.5 mb-1">
                  <Ban className="w-3.5 h-3.5" /> No Account Spoofing
                </strong>
                Connect Gmail accounts or OAuth credentials belonging to third parties without documented authorization.
              </div>
              <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs">
                <strong className="text-red-700 flex items-center gap-1.5 mb-1">
                  <Ban className="w-3.5 h-3.5" /> No System Disruption
                </strong>
                Interfere with, flood, rate-limit, or compromise the integrity of our hosting, database, or API infrastructure.
              </div>
            </div>
          </section>

          <hr className="border-gray-100" />

          {/* Section 7 */}
          <section id="intellectual-property" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">7</span>
              Intellectual Property &amp; Ownership
            </h2>
            <p>
              <strong>Our Software:</strong> The design, codebase, frontend user interfaces, backend classification algorithms, brand assets, and documentation comprising Email Spam Shield are the intellectual property of Lokeshwar L and project contributors, protected under copyright and applicable intellectual property laws.
            </p>
            <p>
              <strong>Your Content:</strong> You retain complete ownership of your email communications, headers, message bodies, and metadata. By connecting your account, you grant us only the limited, temporary license to process, vectorize, and display this data strictly as required to perform the classification service for your authenticated session.
            </p>
          </section>

          <hr className="border-gray-100" />

          {/* Section 8 */}
          <section id="availability-termination" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">8</span>
              Service Availability, Modifications &amp; Termination
            </h2>
            <p>
              We continually improve Email Spam Shield. We reserve the right at any time to:
            </p>
            <ul className="list-disc pl-6 space-y-1 text-gray-600">
              <li>Modify, enhance, or discontinue features, interfaces, or server endpoints.</li>
              <li>Perform scheduled or emergency maintenance leading to temporary service unavailability.</li>
              <li>Suspend or terminate your account access if you breach these Terms or engage in abusive conduct.</li>
            </ul>
            <p>
              You may terminate these Terms at any time by ceasing to use the application, disconnecting your Gmail account, and requesting account deletion.
            </p>
          </section>

          <hr className="border-gray-100" />

          {/* Section 9 */}
          <section id="disclaimer-warranties" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">9</span>
              Disclaimer of Warranties
            </h2>
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl text-xs sm:text-sm text-gray-700 space-y-2 uppercase tracking-wide">
              <p>
                TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, EMAIL SPAM SHIELD IS PROVIDED ON AN &ldquo;AS IS&rdquo; AND &ldquo;AS AVAILABLE&rdquo; BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS, IMPLIED, STATUTORY, OR OTHERWISE.
              </p>
              <p>
                WE SPECIFICALLY DISCLAIM ALL IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, QUIET ENJOYMENT, ACCURACY, AND NON-INFRINGEMENT. WE DO NOT WARRANT THAT THE SERVICE WILL OPERATE UNINTERRUPTED, SECURE, BUG-FREE, OR ERROR-FREE, OR THAT CLASSIFICATION VERDICTS WILL PREVENT ALL HARMFUL MESSAGES.
              </p>
            </div>
          </section>

          <hr className="border-gray-100" />

          {/* Section 10 */}
          <section id="limitation-liability" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">10</span>
              Limitation of Liability
            </h2>
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl text-xs sm:text-sm text-gray-700 space-y-2 uppercase tracking-wide">
              <p>
                IN NO EVENT SHALL EMAIL SPAM SHIELD, ITS DEVELOPER (LOKESHWAR L), CONTRIBUTORS, OR CLOUD SERVICE PROVIDERS (GOOGLE, SUPABASE, RENDER, VERCEL) BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES WHATSOEVER, INCLUDING LOSS OF PROFITS, DATA, USE, GOODWILL, WORK STOPPAGE, OR MISSED COMMUNICATIONS, ARISING OUT OF OR IN CONNECTION WITH YOUR USE OR INABILITY TO USE THE SERVICE.
              </p>
              <p>
                IN NO EVENT SHALL OUR TOTAL CUMULATIVE LIABILITY ARISING OUT OF OR RELATED TO THESE TERMS EXCEED THE GREATER OF FIFTY US DOLLARS ($50.00 USD) OR THE AMOUNT ACTUALLY PAID BY YOU TO USE THE SERVICE IN THE PRECEDING TWELVE MONTHS.
              </p>
            </div>
          </section>

          <hr className="border-gray-100" />

          {/* Section 11 */}
          <section id="governing-law" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">11</span>
              Governing Law &amp; Dispute Resolution
            </h2>
            <p>
              These Terms and any dispute arising out of or related to them shall be governed by and construed in accordance with the laws of India, without regard to conflict of law principles.
            </p>
            <p>
              Prior to initiating formal legal proceedings, you and Email Spam Shield agree to attempt to resolve any dispute, claim, or controversy informally and in good faith by contacting{' '}
              <a href="mailto:lokeshwar6248@gmail.com" className="text-blue-600 hover:underline font-medium">
                lokeshwar6248@gmail.com
              </a>
              .
            </p>
          </section>

          <hr className="border-gray-100" />

          {/* Section 12 */}
          <section id="contact-support" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">12</span>
              Contact Information
            </h2>
            <p>
              For questions regarding these Terms of Service or for developer inquiries:
            </p>
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl text-sm space-y-1.5">
              <p className="font-semibold text-gray-900">Developer &amp; Maintainer:</p>
              <p><strong>Project:</strong> Email Spam Shield (TechTrio Project 1)</p>
              <p><strong>Maintainer:</strong> Lokeshwar L (<code className="text-xs bg-gray-200 px-1 py-0.5 rounded">LokeshtheGreat</code>)</p>
              <p>
                <strong>Email:</strong>{' '}
                <a href="mailto:lokeshwar6248@gmail.com" className="text-blue-600 hover:underline font-medium">
                  lokeshwar6248@gmail.com
                </a>
              </p>
              <p><strong>Repository:</strong>{' '}
                <a href="https://github.com/LokeshtheGreat/TechTrio-Month-2" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-medium">
                  https://github.com/LokeshtheGreat/TechTrio-Month-2
                </a>
              </p>
            </div>
          </section>

        </div>

        {/* Footer Navigation */}
        <div className="mt-12 text-center text-xs text-gray-500 space-y-3">
          <div className="flex items-center justify-center gap-4">
            <a
              href="/"
              onClick={(e) => {
                if (!e.ctrlKey && !e.metaKey && !e.shiftKey && e.button === 0) {
                  e.preventDefault();
                  onNavigate('app');
                }
              }}
              className="hover:text-blue-600 transition-colors"
            >
              App Dashboard
            </a>
            <span>•</span>
            <a
              href="/privacy-policy"
              onClick={(e) => {
                if (!e.ctrlKey && !e.metaKey && !e.shiftKey && e.button === 0) {
                  e.preventDefault();
                  onNavigate('privacy-policy');
                }
              }}
              className="hover:text-blue-600 transition-colors"
            >
              Privacy Policy
            </a>
            <span>•</span>
            <a href="https://github.com/LokeshtheGreat/TechTrio-Month-2" target="_blank" rel="noopener noreferrer" className="hover:text-blue-600 transition-colors">
              GitHub Repository
            </a>
          </div>
          <p>© 2026 Email Spam Shield. All rights reserved.</p>
        </div>
      </main>
    </div>
  );
}
