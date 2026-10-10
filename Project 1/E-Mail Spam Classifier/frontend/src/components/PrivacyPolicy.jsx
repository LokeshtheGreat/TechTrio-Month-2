import React from 'react';
import { Shield, ArrowLeft, Lock, Mail, Database, Server, Eye, Trash2, ExternalLink, FileText, CheckCircle2, AlertCircle } from 'lucide-react';

export default function PrivacyPolicy({ onNavigate }) {
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
              href="/terms"
              onClick={(e) => {
                if (!e.ctrlKey && !e.metaKey && !e.shiftKey && e.button === 0) {
                  e.preventDefault();
                  onNavigate('terms');
                }
              }}
              className="text-xs font-medium text-gray-600 hover:text-blue-600 transition-colors px-2 py-1"
            >
              Terms of Service
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
            <FileText className="w-3.5 h-3.5" />
            <span>Public Legal Document</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight mb-3">
            Privacy Policy
          </h1>
          <p className="text-sm text-gray-500 mb-6">
            <strong>Effective Date:</strong> October 10, 2026 &nbsp;|&nbsp; <strong>Last Updated:</strong> October 10, 2026
          </p>
          <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
            This Privacy Policy explains how <strong>Email Spam Shield</strong> (&ldquo;we&rdquo;, &ldquo;us&rdquo;, or &ldquo;our&rdquo;) collects, uses, processes, stores, and protects your information when you access or use our web application hosted at{' '}
            <a href="https://e-mail-spam-shield.vercel.app/" className="text-blue-600 hover:underline font-medium">
              https://e-mail-spam-shield.vercel.app/
            </a>{' '}
            and connect your Google Gmail account.
          </p>

          <div className="mt-6 p-4 bg-blue-50/70 border border-blue-200/80 rounded-xl text-xs sm:text-sm text-blue-900 flex items-start gap-3">
            <Shield className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold mb-1">Our Core Privacy Commitment</p>
              <p className="text-blue-800 leading-relaxed">
                Email Spam Shield is built solely to classify incoming emails for spam and phishing. We access Gmail in <strong>read-only mode</strong>, execute machine learning inference locally on our servers, encrypt your credentials at rest, never sell your data, and strictly adhere to Google&rsquo;s Limited Use requirements.
              </p>
            </div>
          </div>
        </div>

        {/* Detailed Policy Sections */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 sm:p-10 shadow-sm space-y-10 text-sm sm:text-base leading-relaxed text-gray-700">
          
          {/* Section 1 */}
          <section id="overview" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">1</span>
              What Email Spam Shield Does
            </h2>
            <p>
              Email Spam Shield is an automated security analytics dashboard that helps users identify unsolicited bulk email (spam), promotional clutter, and potential phishing threats. When connected to a user&rsquo;s Gmail account, the system reads incoming messages, analyzes vocabulary and text features through an internal machine learning model, computes a classification verdict (<strong>SPAM</strong> or <strong>HAM</strong>), and displays key indicator tokens in real time on the user&rsquo;s Live Monitor dashboard.
            </p>
          </section>

          <hr className="border-gray-100" />

          {/* Section 2 */}
          <section id="information-collected" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">2</span>
              Information We Collect
            </h2>
            <p>We collect and process the minimum information necessary to provide the spam classification service:</p>
            
            <div className="space-y-3 pl-2">
              <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                <h3 className="font-semibold text-gray-900 text-sm sm:text-base mb-1 flex items-center gap-2">
                  <Lock className="w-4 h-4 text-blue-600" /> Account Information
                </h3>
                <p className="text-sm text-gray-600">
                  When you register for an account using Supabase Authentication, we collect your email address. Passwords are submitted directly to Supabase Auth and are cryptographically hashed; plain passwords are never received, processed, or stored in our application database.
                </p>
              </div>

              <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                <h3 className="font-semibold text-gray-900 text-sm sm:text-base mb-1 flex items-center gap-2">
                  <Mail className="w-4 h-4 text-blue-600" /> Google Account &amp; OAuth Data
                </h3>
                <p className="text-sm text-gray-600">
                  When you connect Gmail, Google OAuth 2.0 provides an OAuth authorization code that we exchange for an access token and refresh token. We also retrieve your primary Gmail email address via the Google profile endpoint. Tokens are strictly encrypted at rest with Fernet (AES-128-CBC + HMAC-SHA256) before storage.
                </p>
              </div>
            </div>
          </section>

          <hr className="border-gray-100" />

          {/* Section 3 */}
          <section id="gmail-access" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">3</span>
              Gmail Access &amp; The <code className="text-base text-blue-700 bg-blue-50 px-2 py-0.5 rounded font-mono">gmail.readonly</code> Scope
            </h2>
            <p>
              Email Spam Shield requests a single restricted OAuth scope:
            </p>
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg font-mono text-xs sm:text-sm text-blue-900 break-all">
              https://www.googleapis.com/auth/gmail.readonly
            </div>
            <p>
              <strong>Exact Purpose:</strong> This permission is used exclusively to fetch message metadata and content for the purpose of classifying whether emails are spam or legitimate messages.
            </p>
            <p>
              <strong>What We Do NOT Do:</strong>
            </p>
            <ul className="list-disc pl-6 space-y-1 text-sm text-gray-600">
              <li>We <strong>never</strong> request or obtain permission to send emails (<code className="font-mono text-xs">gmail.send</code>).</li>
              <li>We <strong>never</strong> request or obtain permission to compose or draft emails (<code className="font-mono text-xs">gmail.compose</code>).</li>
              <li>We <strong>never</strong> modify, delete, mark as read, or move emails in your Gmail inbox (<code className="font-mono text-xs">gmail.modify</code>).</li>
              <li>We <strong>never</strong> modify your Gmail labels, filters, forwarding rules, or account settings.</li>
            </ul>
          </section>

          <hr className="border-gray-100" />

          {/* Section 4 */}
          <section id="email-processing" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">4</span>
              How Email Content &amp; Attachments Are Processed
            </h2>
            <p>
              When a new message notification is received or a sync is requested:
            </p>
            <ol className="list-decimal pl-6 space-y-2 text-sm text-gray-600">
              <li>
                <strong>Message Retrieval:</strong> The backend queries the Gmail REST API for the message using its unique message ID.
              </li>
              <li>
                <strong>Text Extraction:</strong> The system parses MIME body parts to extract plain text (<code className="font-mono text-xs">text/plain</code>) and HTML (<code className="font-mono text-xs">text/html</code>).
              </li>
              <li>
                <strong>Attachment Exclusion:</strong> <strong className="text-gray-900">Attachments are strictly ignored.</strong> Our parser specifically skips any MIME part containing a filename attribute. File attachments (PDFs, images, ZIP files, executables, documents) are never downloaded, opened, analyzed, or stored on our servers.
              </li>
              <li>
                <strong>Local Machine Learning Inference:</strong> Extracted message text is tokenized with TF-IDF and evaluated by a pre-trained Linear Support Vector Machine (<code className="font-mono text-xs">LinearSVC</code>) model hosted directly in the Flask server application.
              </li>
              <li>
                <strong>No Third-Party AI Transmission:</strong> Your email text is <strong>never</strong> transmitted to external third-party language models or commercial AI APIs (e.g., OpenAI, Anthropic, or external cloud LLMs). All spam scoring occurs locally in memory.
              </li>
            </ol>
          </section>

          <hr className="border-gray-100" />

          {/* Section 5 */}
          <section id="storage-retention" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">5</span>
              What Data Is Stored &amp; How Long It Is Retained
            </h2>
            <p>
              To maintain transparency, the exact database records stored in our PostgreSQL database (<code className="font-mono text-xs">classified_emails</code> and <code className="font-mono text-xs">gmail_connections</code>) are listed below:
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs sm:text-sm border border-gray-200 rounded-lg overflow-hidden">
                <thead className="bg-gray-100 text-gray-700 font-semibold">
                  <tr>
                    <th className="p-3 border-b border-gray-200">Data Field</th>
                    <th className="p-3 border-b border-gray-200">Description</th>
                    <th className="p-3 border-b border-gray-200">Purpose</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 text-gray-600">
                  <tr>
                    <td className="p-3 font-mono font-medium text-gray-900">user_id</td>
                    <td className="p-3">Your unique Supabase account UUID</td>
                    <td className="p-3">Multi-user account isolation</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-mono font-medium text-gray-900">message_id</td>
                    <td className="p-3">Gmail message identifier</td>
                    <td className="p-3">Deduplication &amp; change tracking</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-mono font-medium text-gray-900">sender, subject, timestamp</td>
                    <td className="p-3">Email header metadata</td>
                    <td className="p-3">Displayed on email cards in Live Monitor</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-mono font-medium text-gray-900">snippet, body, body_html</td>
                    <td className="p-3">Extracted plaintext and HTML text</td>
                    <td className="p-3">Viewing email content and indicators in dashboard</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-mono font-medium text-gray-900">prediction, strength, spam_indicators</td>
                    <td className="p-3">SPAM/HAM verdict, confidence score, tokens</td>
                    <td className="p-3">Spam Shield classification display</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-mono font-medium text-gray-900">encrypted_credentials_json</td>
                    <td className="p-3">Fernet-encrypted Google OAuth tokens</td>
                    <td className="p-3">Authorized access to Gmail API</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="text-sm">
              <strong>Retention Period:</strong> These records are retained in your private user space for as long as your account remains active and connected. You can delete or disconnect them at any time as described in Section 9.
            </p>
          </section>

          <hr className="border-gray-100" />

          {/* Section 6 */}
          <section id="third-parties" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">6</span>
              Third-Party Infrastructure Services
            </h2>
            <p>
              We rely only on reputable cloud infrastructure providers to run our service. Each provider processes data solely as directed by our application:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div className="p-4 bg-gray-50 border border-gray-100 rounded-xl">
                <h3 className="font-semibold text-gray-900 mb-1 flex items-center gap-1.5">
                  <Server className="w-4 h-4 text-blue-600" /> Google Cloud Platform
                </h3>
                <p className="text-gray-600 text-xs">
                  Provides Google OAuth 2.0 authentication, the Gmail REST API, and Google Cloud Pub/Sub push notifications.
                </p>
              </div>
              <div className="p-4 bg-gray-50 border border-gray-100 rounded-xl">
                <h3 className="font-semibold text-gray-900 mb-1 flex items-center gap-1.5">
                  <Database className="w-4 h-4 text-blue-600" /> Supabase
                </h3>
                <p className="text-gray-600 text-xs">
                  Hosts our managed PostgreSQL database and handles secure user authentication sessions.
                </p>
              </div>
              <div className="p-4 bg-gray-50 border border-gray-100 rounded-xl">
                <h3 className="font-semibold text-gray-900 mb-1 flex items-center gap-1.5">
                  <Server className="w-4 h-4 text-blue-600" /> Render
                </h3>
                <p className="text-gray-600 text-xs">
                  Hosts the Flask Python backend application and executes spam classification inference in a sandboxed container.
                </p>
              </div>
              <div className="p-4 bg-gray-50 border border-gray-100 rounded-xl">
                <h3 className="font-semibold text-gray-900 mb-1 flex items-center gap-1.5">
                  <ExternalLink className="w-4 h-4 text-blue-600" /> Vercel
                </h3>
                <p className="text-gray-600 text-xs">
                  Hosts the frontend React single-page application and static web assets on a global edge CDN.
                </p>
              </div>
            </div>
          </section>

          <hr className="border-gray-100" />

          {/* Section 7 */}
          <section id="data-sharing" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">7</span>
              Data Sharing &amp; Transfer
            </h2>
            <div className="space-y-2">
              <p className="font-semibold text-gray-900">
                We do NOT sell, lease, trade, or monetize your personal data or email contents under any circumstances.
              </p>
              <p>
                We do not transfer user data to advertising networks, data brokers, or commercial marketing platforms. Data is only transferred:
              </p>
              <ul className="list-disc pl-6 space-y-1 text-sm text-gray-600">
                <li>To our verified cloud infrastructure partners (Google, Supabase, Render, Vercel) strictly to deliver the service.</li>
                <li>When required by law, subpoena, court order, or official governmental request.</li>
                <li>To investigate fraud, security vulnerabilities, or violations of our Terms of Service.</li>
              </ul>
            </div>
          </section>

          <hr className="border-gray-100" />

          {/* Section 8 - GOOGLE LIMITED USE (MANDATORY) */}
          <section id="google-limited-use" className="space-y-4 bg-blue-50/50 p-6 rounded-2xl border border-blue-200">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <CheckCircle2 className="w-6 h-6 text-blue-600 flex-shrink-0" />
              Google API Services User Data Policy &amp; Limited Use Disclosure
            </h2>
            
            <div className="p-4 bg-white border-l-4 border-blue-600 rounded-r-xl shadow-xs text-sm sm:text-base font-semibold text-gray-900 leading-relaxed">
              &ldquo;Email Spam Shield's use and transfer to any other app of information received from Google APIs will adhere to the Google API Services User Data Policy, including the Limited Use requirements.&rdquo;
            </div>

            <p className="text-xs text-gray-500">
              Read the official requirements directly on Google's Developer portal:{' '}
              <a
                href="https://developers.google.com/terms/api-services-user-data-policy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-700 underline font-semibold hover:text-blue-900 inline-flex items-center gap-1"
              >
                Google API Services User Data Policy
                <ExternalLink className="w-3.5 h-3.5 inline" />
              </a>
              .
            </p>

            <div className="space-y-2 text-sm text-gray-700">
              <p className="font-semibold text-gray-900">Specifically, in accordance with Google Limited Use requirements:</p>
              <ul className="list-disc pl-6 space-y-1.5">
                <li>
                  <strong>User-Facing Features Only:</strong> We only use access to read Gmail data to provide customer-facing spam analysis and email monitoring within the Email Spam Shield application.
                </li>
                <li>
                  <strong>No Transfer:</strong> We do not transfer this data to third parties, other than to our trusted service providers (Render, Supabase) as necessary to provide or improve these user-facing features.
                </li>
                <li>
                  <strong>No Advertising:</strong> We do not use or transfer this data for serving advertisements, including personalized, re-targeted, or interest-based advertising.
                </li>
                <li>
                  <strong>No Human Viewing:</strong> We do not permit humans to read your email data unless:
                  <ul className="list-circle pl-6 mt-1 space-y-1 text-xs sm:text-sm text-gray-600">
                    <li>We have obtained your explicit affirmative agreement for specific messages (for example, if you request customer support regarding a specific email classification error);</li>
                    <li>It is strictly necessary for security purposes (such as investigating abuse or diagnosing a system bug);</li>
                    <li>It is necessary to comply with applicable laws; or</li>
                    <li>The data has been aggregated and anonymized for internal technical operations.</li>
                  </ul>
                </li>
                <li>
                  <strong>No Generalized AI Model Training:</strong> We do not use Google user data to train, retrain, or improve generalized machine learning or artificial intelligence models without your separate, explicit consent.
                </li>
              </ul>
            </div>
          </section>

          <hr className="border-gray-100" />

          {/* Section 9 */}
          <section id="user-rights" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">9</span>
              User Controls, Consent Revocation &amp; Data Deletion
            </h2>
            <p>You have complete control over your Gmail connection and stored data:</p>

            <div className="space-y-3 pl-2">
              <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                <h3 className="font-semibold text-gray-900 text-sm sm:text-base mb-1 flex items-center gap-2">
                  <Trash2 className="w-4 h-4 text-red-600" /> Disconnecting Gmail in the App
                </h3>
                <p className="text-sm text-gray-600">
                  You can click the <strong>&ldquo;Disconnect Gmail&rdquo;</strong> button directly in the Live Monitor interface at any time. This action calls our backend, stops real-time watch subscriptions, and permanently deletes your stored Google OAuth credentials (<code className="font-mono text-xs">encrypted_credentials_json</code>) from our database.
                </p>
              </div>

              <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                <h3 className="font-semibold text-gray-900 text-sm sm:text-base mb-1 flex items-center gap-2">
                  <ExternalLink className="w-4 h-4 text-blue-600" /> Revoking Access via Google
                </h3>
                <p className="text-sm text-gray-600">
                  You can revoke Email Spam Shield&rsquo;s access to your Google Account at any time directly through your{' '}
                  <a
                    href="https://myaccount.google.com/permissions"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline font-medium inline-flex items-center gap-1"
                  >
                    Google Account Security Permissions
                    <ExternalLink className="w-3 h-3 inline" />
                  </a>
                  . Once revoked, our application can never access your mailbox again.
                </p>
              </div>

              <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                <h3 className="font-semibold text-gray-900 text-sm sm:text-base mb-1 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-purple-600" /> Full Account &amp; Stored Email Deletion
                </h3>
                <p className="text-sm text-gray-600">
                  If you wish to delete your entire account, all classified email records, and all associated metadata, you can submit a deletion request to{' '}
                  <a href="mailto:lokeshwar6248@gmail.com" className="text-blue-600 hover:underline font-medium">
                    lokeshwar6248@gmail.com
                  </a>
                  . Our database enforces cascading deletion (<code className="font-mono text-xs">ON DELETE CASCADE</code>), ensuring all associated records are permanently purged upon account removal.
                </p>
              </div>
            </div>
          </section>

          <hr className="border-gray-100" />

          {/* Section 10 */}
          <section id="contact" className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">10</span>
              Contact Information &amp; Policy Updates
            </h2>
            <p>
              We may update this Privacy Policy from time to time to reflect changes in our legal obligations, software updates, or cloud architecture. When updates are published, the &ldquo;Last Updated&rdquo; date at the top of this document will be revised.
            </p>
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl text-sm space-y-1.5">
              <p className="font-semibold text-gray-900">Developer &amp; Privacy Contact:</p>
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
              href="/terms"
              onClick={(e) => {
                if (!e.ctrlKey && !e.metaKey && !e.shiftKey && e.button === 0) {
                  e.preventDefault();
                  onNavigate('terms');
                }
              }}
              className="hover:text-blue-600 transition-colors"
            >
              Terms of Service
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
