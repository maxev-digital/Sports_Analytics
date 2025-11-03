import { Navigation } from '../components/Navigation';
import { Footer } from '../components/Footer';

export function Privacy() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white flex flex-col">
      <Navigation />

      <main className="flex-1 container mx-auto px-4 py-12 max-w-5xl">
        <h1 className="text-4xl font-bold text-yellow-400 mb-2">Privacy Policy</h1>
        <p className="text-slate-400 mb-8">Last Updated: January 2, 2025</p>

        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 space-y-6 text-slate-300 leading-relaxed">

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">1. Introduction</h2>
            <p>
              <strong>Max EV Holdings, LLC</strong> (a Wyoming Limited Liability Company, Filing ID: 2025-001800389) ("we," "us," or "our")
              operates Max EV Sports. This Privacy Policy explains how we collect, use, disclose, and protect your personal information
              when you use our Platform.
            </p>
            <p className="mt-3">
              By using Max EV Sports, you consent to the collection and use of your information as described in this Privacy Policy.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">2. Information We Collect</h2>

            <h3 className="text-xl font-semibold text-white mb-2">2.1 Information You Provide</h3>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Account Information:</strong> Username, email address, password</li>
              <li><strong>Payment Information:</strong> Processed through Stripe (we do not store full credit card details)</li>
              <li><strong>Profile Data:</strong> Betting preferences, favorite sports, subscription tier</li>
              <li><strong>Betting Tracking Data:</strong> Bets you log, stakes, outcomes, and performance metrics</li>
              <li><strong>Communication Data:</strong> Support requests, feedback, and correspondence</li>
            </ul>

            <h3 className="text-xl font-semibold text-white mt-4 mb-2">2.2 Automatically Collected Information</h3>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Usage Data:</strong> Pages viewed, features used, alerts clicked, time spent on Platform</li>
              <li><strong>Device Information:</strong> Browser type, operating system, IP address, device identifiers</li>
              <li><strong>Log Data:</strong> Access times, error logs, referring URLs</li>
              <li><strong>Cookies and Tracking:</strong> Session cookies, authentication tokens, analytics cookies</li>
            </ul>

            <h3 className="text-xl font-semibold text-white mt-4 mb-2">2.3 Third-Party Data</h3>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Odds Data:</strong> Real-time odds from The Odds API and other providers</li>
              <li><strong>Social Media:</strong> If you connect social accounts (optional)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">3. How We Use Your Information</h2>
            <p className="mb-3">We use your information to:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Provide Services:</strong> Deliver alerts, analytics, and betting tracking features</li>
              <li><strong>Account Management:</strong> Maintain your account, process subscriptions, and handle billing</li>
              <li><strong>Personalization:</strong> Customize alerts and content based on your preferences and betting history</li>
              <li><strong>Communication:</strong> Send important updates, alerts, newsletters, and respond to support requests</li>
              <li><strong>Analytics:</strong> Analyze usage patterns to improve the Platform and develop new features</li>
              <li><strong>Security:</strong> Detect fraud, prevent abuse, and protect user accounts</li>
              <li><strong>Legal Compliance:</strong> Comply with applicable laws and regulations</li>
              <li><strong>Marketing:</strong> Send promotional content (with your consent, and you may opt out)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">4. How We Share Your Information</h2>
            <p className="mb-3">We may share your information with:</p>

            <h3 className="text-xl font-semibold text-white mb-2">4.1 Service Providers</h3>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Payment Processing:</strong> Stripe for subscription billing</li>
              <li><strong>Email Services:</strong> Brevo for transactional and marketing emails</li>
              <li><strong>Analytics:</strong> Google Analytics, Mixpanel, or similar services</li>
              <li><strong>Hosting:</strong> Cloud infrastructure providers</li>
              <li><strong>Customer Support:</strong> Help desk and support ticketing systems</li>
            </ul>

            <h3 className="text-xl font-semibold text-white mt-4 mb-2">4.2 Business Transfers</h3>
            <p>
              If we undergo a merger, acquisition, or sale of assets, your information may be transferred as part of that transaction.
            </p>

            <h3 className="text-xl font-semibold text-white mt-4 mb-2">4.3 Legal Requirements</h3>
            <p>We may disclose your information if required by law, court order, or government request, or to:</p>
            <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
              <li>Enforce our Terms of Service</li>
              <li>Protect our rights, property, or safety</li>
              <li>Prevent fraud or illegal activity</li>
              <li>Respond to legal claims</li>
            </ul>

            <h3 className="text-xl font-semibold text-white mt-4 mb-2">4.4 Aggregate Data</h3>
            <p>
              We may share anonymized, aggregated data that cannot identify you personally for research, analytics, or marketing purposes.
            </p>

            <p className="mt-4 text-yellow-400 font-semibold">
              We DO NOT sell your personal information to third parties.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">5. Cookies and Tracking Technologies</h2>
            <p className="mb-3">We use cookies and similar technologies to:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Keep you logged in</li>
              <li>Remember your preferences</li>
              <li>Analyze usage and performance</li>
              <li>Deliver targeted content</li>
            </ul>
            <p className="mt-3">
              You can control cookies through your browser settings. However, disabling cookies may limit Platform functionality.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">6. Data Security</h2>
            <p className="mb-3">We implement industry-standard security measures including:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Encryption of data in transit (HTTPS/TLS)</li>
              <li>Secure password hashing</li>
              <li>Regular security audits</li>
              <li>Access controls and authentication</li>
              <li>Secure cloud infrastructure</li>
            </ul>
            <p className="mt-3">
              <strong className="text-yellow-400">However, no system is 100% secure.</strong> We cannot guarantee absolute security
              of your information. You are responsible for maintaining the confidentiality of your account credentials.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">7. Data Retention</h2>
            <p>We retain your information for as long as:</p>
            <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
              <li>Your account is active</li>
              <li>Needed to provide services</li>
              <li>Required by law or for legitimate business purposes</li>
              <li>Necessary to resolve disputes or enforce agreements</li>
            </ul>
            <p className="mt-3">
              After account deletion, we may retain anonymized data for analytics and certain information for legal compliance.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">8. Your Privacy Rights</h2>
            <p className="mb-3">You have the right to:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Access:</strong> Request a copy of your personal information</li>
              <li><strong>Correction:</strong> Update or correct inaccurate information</li>
              <li><strong>Deletion:</strong> Request deletion of your account and data</li>
              <li><strong>Opt-Out:</strong> Unsubscribe from marketing emails</li>
              <li><strong>Data Portability:</strong> Receive your data in a structured format</li>
              <li><strong>Objection:</strong> Object to processing of your data for certain purposes</li>
            </ul>
            <p className="mt-3">
              To exercise these rights, contact us at <a href="mailto:support@max-ev-sports.com" className="text-yellow-400 underline hover:text-yellow-300">support@max-ev-sports.com</a>
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">9. Children's Privacy</h2>
            <p>
              Our Platform is not intended for individuals under 21 years of age (or the legal gambling age in your jurisdiction).
              We do not knowingly collect information from minors. If we discover we have collected information from a minor,
              we will delete it immediately.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">10. International Users</h2>
            <p>
              Our Platform is operated in the United States. If you access the Platform from outside the U.S., your information
              will be transferred to, stored, and processed in the United States. By using the Platform, you consent to this transfer.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">11. California Privacy Rights (CCPA)</h2>
            <p className="mb-3">California residents have additional rights under the California Consumer Privacy Act (CCPA):</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Right to know what personal information is collected</li>
              <li>Right to know if personal information is sold or disclosed</li>
              <li>Right to opt-out of the sale of personal information</li>
              <li>Right to deletion of personal information</li>
              <li>Right to non-discrimination for exercising CCPA rights</li>
            </ul>
            <p className="mt-3 text-yellow-400 font-semibold">
              We do not sell personal information.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">12. European Users (GDPR)</h2>
            <p className="mb-3">If you are in the European Economic Area (EEA), you have rights under the General Data Protection Regulation (GDPR):</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Right to access your personal data</li>
              <li>Right to rectification of inaccurate data</li>
              <li>Right to erasure ("right to be forgotten")</li>
              <li>Right to restrict processing</li>
              <li>Right to data portability</li>
              <li>Right to object to processing</li>
            </ul>
            <p className="mt-3">
              Our legal basis for processing includes your consent, performance of contract, and legitimate interests.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">13. Do Not Track Signals</h2>
            <p>
              Some browsers have "Do Not Track" features. We do not currently respond to Do Not Track signals.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">14. Third-Party Links</h2>
            <p>
              Our Platform contains links to third-party sportsbooks and services. We are not responsible for the privacy
              practices of these third parties. Please review their privacy policies.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">15. Changes to This Privacy Policy</h2>
            <p>
              We may update this Privacy Policy from time to time. We will notify you of significant changes by posting a
              notice on the Platform or sending an email. Your continued use after changes constitutes acceptance of the updated policy.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">16. Contact Us</h2>
            <p>
              If you have questions about this Privacy Policy or our data practices, please contact us:
            </p>
            <div className="mt-2 ml-4">
              <p><strong>Max EV Holdings, LLC</strong></p>
              <p>Email: <a href="mailto:support@max-ev-sports.com" className="text-yellow-400 underline hover:text-yellow-300">support@max-ev-sports.com</a></p>
              <p className="mt-2">Wyoming Limited Liability Company</p>
              <p>Filing ID: 2025-001800389</p>
            </div>
          </section>

        </div>
      </main>

      <Footer />
    </div>
  );
}
