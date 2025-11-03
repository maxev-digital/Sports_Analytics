import { Navigation } from '../components/Navigation';
import { Footer } from '../components/Footer';

export function Terms() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white flex flex-col">
      <Navigation />

      <main className="flex-1 container mx-auto px-4 py-12 max-w-5xl">
        <h1 className="text-4xl font-bold text-yellow-400 mb-2">Terms of Service</h1>
        <p className="text-slate-400 mb-8">Last Updated: January 2, 2025</p>

        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 space-y-6 text-slate-300 leading-relaxed">

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">1. Agreement to Terms</h2>
            <p>
              By accessing or using Max EV Sports ("the Platform"), operated by <strong>Max EV Holdings, LLC</strong>
              (a Wyoming Limited Liability Company, Filing ID: 2025-001800389), you agree to be bound by these Terms of Service.
              If you do not agree to these terms, you must not access or use the Platform.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">2. Description of Service</h2>
            <p className="mb-3">
              Max EV Sports provides sports betting analytics, odds comparison, alerts, and educational content including:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Real-time arbitrage opportunities detection</li>
              <li>Steam move alerts and line movement tracking</li>
              <li>Middle betting opportunities</li>
              <li>Live betting analytics and predictions</li>
              <li>Betting performance tracking tools</li>
              <li>Educational articles and strategy guides</li>
            </ul>
            <p className="mt-3">
              <strong className="text-yellow-400">We DO NOT accept, place, or facilitate any bets.</strong> We are an
              informational service only. All betting is conducted through third-party licensed sportsbooks.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">3. Age Requirement</h2>
            <p>
              You must be <strong>21 years of age or older</strong> (or the legal gambling age in your jurisdiction, whichever is greater)
              to use this Platform. By using the Platform, you represent and warrant that you meet this age requirement.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">4. Geographic Restrictions</h2>
            <p className="mb-3">
              Sports betting laws vary by jurisdiction. You are solely responsible for ensuring that your use of this Platform
              and any betting activities comply with all applicable laws in your location. Use of this Platform is prohibited in
              jurisdictions where sports betting analytics services or sports betting itself is illegal.
            </p>
            <p className="text-yellow-400 font-semibold">
              You must not use this Platform if you are located in a jurisdiction where such use is prohibited by law.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">5. No Guarantees or Warranties</h2>
            <p className="mb-3">
              <strong>THE PLATFORM AND ALL CONTENT, ALERTS, AND ANALYTICS ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND.</strong>
            </p>
            <p>We explicitly disclaim all warranties including but not limited to:</p>
            <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
              <li>Accuracy of odds, alerts, or predictions</li>
              <li>Timeliness of information</li>
              <li>Profitability of any alerts or strategies</li>
              <li>Fitness for any particular purpose</li>
              <li>Uninterrupted or error-free service</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">6. Not Financial or Gambling Advice</h2>
            <p className="mb-3">
              <strong className="text-red-400">NOTHING ON THIS PLATFORM CONSTITUTES FINANCIAL, INVESTMENT, OR GAMBLING ADVICE.</strong>
            </p>
            <p>
              All content is provided for informational and educational purposes only. You are solely responsible for your
              betting decisions. Past performance of alerts, strategies, or predictions does not guarantee future results.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">7. User Accounts and Subscriptions</h2>
            <h3 className="text-xl font-semibold text-white mb-2">7.1 Account Security</h3>
            <p className="mb-3">
              You are responsible for maintaining the confidentiality of your account credentials. You agree to notify us
              immediately of any unauthorized use of your account.
            </p>

            <h3 className="text-xl font-semibold text-white mb-2">7.2 Subscription Terms</h3>
            <p className="mb-2">Paid subscriptions:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Are billed monthly or annually as selected</li>
              <li>Automatically renew unless cancelled prior to renewal date</li>
              <li>Are non-refundable except as required by law</li>
              <li>May be cancelled at any time through your account settings</li>
            </ul>

            <h3 className="text-xl font-semibold text-white mt-3 mb-2">7.3 Free Trial</h3>
            <p>
              If a free trial is offered, you may cancel before the trial period ends to avoid charges. Failure to cancel
              will result in automatic billing for the selected subscription plan.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">8. Acceptable Use</h2>
            <p className="mb-2">You agree NOT to:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Use the Platform for any illegal purpose</li>
              <li>Scrape, copy, or redistribute our data without permission</li>
              <li>Reverse engineer or attempt to access source code</li>
              <li>Share your account credentials with others</li>
              <li>Use automated tools to access the Platform without authorization</li>
              <li>Interfere with or disrupt the Platform's operation</li>
              <li>Impersonate any person or entity</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">9. Intellectual Property</h2>
            <p>
              All content, features, functionality, alerts, analytics algorithms, and design of the Platform are owned by
              Max EV Holdings, LLC and are protected by United States and international copyright, trademark, and other
              intellectual property laws. You may not reproduce, distribute, or create derivative works without express written permission.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">10. Third-Party Links and Services</h2>
            <p>
              The Platform contains links to third-party sportsbooks and services. We are not responsible for the content,
              terms, or privacy practices of these third parties. Your interactions with third-party sportsbooks are governed
              by their respective terms and conditions.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">11. Limitation of Liability</h2>
            <p className="mb-3">
              <strong className="text-red-400">TO THE MAXIMUM EXTENT PERMITTED BY LAW, MAX EV HOLDINGS, LLC SHALL NOT BE LIABLE FOR:</strong>
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Any betting losses incurred based on information from the Platform</li>
              <li>Inaccurate odds, alerts, or analytics</li>
              <li>Service interruptions or technical errors</li>
              <li>Unauthorized access to your account</li>
              <li>Any indirect, incidental, special, or consequential damages</li>
            </ul>
            <p className="mt-3">
              In no event shall our total liability exceed the amount you paid for subscription services in the 12 months
              preceding the claim.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">12. Indemnification</h2>
            <p>
              You agree to indemnify and hold harmless Max EV Holdings, LLC, its officers, directors, employees, and agents
              from any claims, damages, losses, or expenses (including attorneys' fees) arising from:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
              <li>Your use of the Platform</li>
              <li>Your betting activities</li>
              <li>Your violation of these Terms</li>
              <li>Your violation of any applicable laws</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">13. Modifications to Service and Terms</h2>
            <p>
              We reserve the right to modify or discontinue the Platform (or any part thereof) at any time without notice.
              We may also update these Terms at any time. Continued use of the Platform after changes constitutes acceptance
              of the modified Terms.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">14. Termination</h2>
            <p>
              We may terminate or suspend your account and access to the Platform immediately, without prior notice, for any
              reason including breach of these Terms. Upon termination, your right to use the Platform will immediately cease.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">15. Governing Law and Dispute Resolution</h2>
            <h3 className="text-xl font-semibold text-white mb-2">15.1 Governing Law</h3>
            <p className="mb-3">
              These Terms shall be governed by the laws of the State of Wyoming, without regard to conflict of law principles.
            </p>

            <h3 className="text-xl font-semibold text-white mb-2">15.2 Arbitration Agreement</h3>
            <p className="mb-3">
              Any dispute arising out of or relating to these Terms or the Platform shall be resolved through binding arbitration
              in accordance with the American Arbitration Association rules. You waive your right to a jury trial or to participate
              in a class action lawsuit.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">16. Responsible Gambling</h2>
            <p>
              We encourage responsible gambling. If you or someone you know has a gambling problem, please seek help:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
              <li><strong>National Council on Problem Gambling:</strong> 1-800-GAMBLER</li>
              <li><strong>Website:</strong> <a href="https://www.ncpgambling.org" className="text-yellow-400 underline hover:text-yellow-300" target="_blank" rel="noopener noreferrer">ncpgambling.org</a></li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">17. Contact Information</h2>
            <p>
              For questions about these Terms, please contact us at:
            </p>
            <div className="mt-2 ml-4">
              <p><strong>Max EV Holdings, LLC</strong></p>
              <p>Email: <a href="mailto:support@max-ev-sports.com" className="text-yellow-400 underline hover:text-yellow-300">support@max-ev-sports.com</a></p>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">18. Severability</h2>
            <p>
              If any provision of these Terms is found to be unenforceable, the remaining provisions will continue in full force and effect.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">19. Entire Agreement</h2>
            <p>
              These Terms, together with our Privacy Policy and Disclaimer, constitute the entire agreement between you and
              Max EV Holdings, LLC regarding use of the Platform.
            </p>
          </section>

        </div>
      </main>

      <Footer />
    </div>
  );
}
