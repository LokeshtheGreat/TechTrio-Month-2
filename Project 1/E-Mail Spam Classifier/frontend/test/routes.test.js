import test, { describe } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { getRouteFromUrl, getRoutePath } from '../src/utils/routes.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

describe('Client-Side SPA Routing & Legal URLs', () => {
  test('resolves /privacy-policy and /privacy pathname to privacy-policy route', () => {
    assert.equal(getRouteFromUrl({ pathname: '/privacy-policy', hash: '' }), 'privacy-policy');
    assert.equal(getRouteFromUrl({ pathname: '/privacy-policy/', hash: '' }), 'privacy-policy');
    assert.equal(getRouteFromUrl({ pathname: '/privacy', hash: '' }), 'privacy-policy');
  });

  test('resolves #/privacy-policy and #privacy hash to privacy-policy route', () => {
    assert.equal(getRouteFromUrl({ pathname: '/', hash: '#/privacy-policy' }), 'privacy-policy');
    assert.equal(getRouteFromUrl({ pathname: '/', hash: '#privacy-policy' }), 'privacy-policy');
    assert.equal(getRouteFromUrl({ pathname: '/', hash: '#/privacy' }), 'privacy-policy');
  });

  test('resolves /terms and /terms-of-service pathname to terms route', () => {
    assert.equal(getRouteFromUrl({ pathname: '/terms', hash: '' }), 'terms');
    assert.equal(getRouteFromUrl({ pathname: '/terms/', hash: '' }), 'terms');
    assert.equal(getRouteFromUrl({ pathname: '/terms-of-service', hash: '' }), 'terms');
  });

  test('resolves #/terms and #terms hash to terms route', () => {
    assert.equal(getRouteFromUrl({ pathname: '/', hash: '#/terms' }), 'terms');
    assert.equal(getRouteFromUrl({ pathname: '/', hash: '#terms' }), 'terms');
    assert.equal(getRouteFromUrl({ pathname: '/', hash: '#/terms-of-service' }), 'terms');
  });

  test('falls back to app route for root, unknown paths, or empty location', () => {
    assert.equal(getRouteFromUrl({ pathname: '/', hash: '' }), 'app');
    assert.equal(getRouteFromUrl({ pathname: '/unknown-route', hash: '' }), 'app');
    assert.equal(getRouteFromUrl(null), 'app');
  });

  test('getRoutePath returns canonical URL pathnames', () => {
    assert.equal(getRoutePath('privacy-policy'), '/privacy-policy');
    assert.equal(getRoutePath('terms'), '/terms');
    assert.equal(getRoutePath('app'), '/');
  });
});

describe('Legal Documents Content & Google Compliance Audit', () => {
  const privacyPath = path.resolve(__dirname, '../src/components/PrivacyPolicy.jsx');
  const termsPath = path.resolve(__dirname, '../src/components/TermsOfService.jsx');
  const vercelPath = path.resolve(__dirname, '../vercel.json');

  test('PrivacyPolicy.jsx exists and includes exact required Google Limited Use disclosure', () => {
    assert.ok(fs.existsSync(privacyPath), 'PrivacyPolicy.jsx must exist');
    const content = fs.readFileSync(privacyPath, 'utf8');

    // Normalize JSX tags, HTML entities, and whitespace for text comparison
    const normalizedText = content
      .replace(/<[^>]+>/g, ' ')
      .replace(/&rsquo;/g, "'")
      .replace(/&lsquo;/g, "'")
      .replace(/&rdquo;/g, '"')
      .replace(/&ldquo;/g, '"')
      .replace(/&amp;/g, '&')
      .replace(/\s+/g, ' ');

    // Google OAuth Verification required verbatim text
    const requiredLimitedUse = "Email Spam Shield's use and transfer to any other app of information received from Google APIs will adhere to the Google API Services User Data Policy, including the Limited Use requirements.";
    assert.ok(
      normalizedText.includes(requiredLimitedUse),
      'PrivacyPolicy must contain the verbatim Google Limited Use disclosure'
    );

    // Readonly OAuth scope
    assert.ok(
      content.includes('https://www.googleapis.com/auth/gmail.readonly'),
      'PrivacyPolicy must declare gmail.readonly scope'
    );

    // Critical privacy guarantees
    assert.ok(content.includes('Local Machine Learning Inference'), 'Must mention local machine learning inference');
    assert.ok(content.includes('Attachments are strictly ignored') || content.includes('never downloaded'), 'Must confirm attachment exclusion');
    assert.ok(content.includes('lokeshwar6248@gmail.com'), 'Must list maintainer contact email');
  });

  test('TermsOfService.jsx exists and includes ML limitations and user verification responsibility', () => {
    assert.ok(fs.existsSync(termsPath), 'TermsOfService.jsx must exist');
    const content = fs.readFileSync(termsPath, 'utf8');

    // Model disclaimer
    assert.ok(
      content.includes('probabilistic'),
      'TermsOfService must state that ML predictions are probabilistic'
    );
    assert.ok(
      content.includes('false positives') && content.includes('false negatives'),
      'TermsOfService must warn about false positives and false negatives'
    );
    assert.ok(
      content.includes('User Responsibility to Verify Critical Communications'),
      'TermsOfService must explicitly state user verification responsibility'
    );
    assert.ok(
      content.includes('DISCLAIMER OF WARRANTIES') || content.includes('Disclaimer of Warranties'),
      'TermsOfService must include disclaimer of warranties'
    );
    assert.ok(
      content.includes('LIMITATION OF LIABILITY') || content.includes('Limitation of Liability'),
      'TermsOfService must include limitation of liability'
    );
    assert.ok(content.includes('lokeshwar6248@gmail.com'), 'Must list maintainer contact email');
  });

  test('vercel.json exists and configures SPA rewrites for deep links while preserving API routing', () => {
    assert.ok(fs.existsSync(vercelPath), 'vercel.json must exist');
    const config = JSON.parse(fs.readFileSync(vercelPath, 'utf8'));
    assert.ok(Array.isArray(config.rewrites), 'rewrites array must be defined');

    const hasApiRewrite = config.rewrites.some(
      (r) => r.source.startsWith('/api') && r.destination.includes('onrender.com')
    );
    assert.ok(hasApiRewrite, 'API routes must be preserved and forwarded to Render backend');

    const lastRule = config.rewrites[config.rewrites.length - 1];
    assert.equal(lastRule.source, '/(.*)', 'Final rewrite rule must be catch-all');
    assert.equal(lastRule.destination, '/index.html', 'Catch-all rule must route to /index.html');
  });
});
