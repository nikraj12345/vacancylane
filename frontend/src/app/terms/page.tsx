"use client";

import { AppShell } from "@/components/app-shell";

export default function TermsPage() {
  return (
    <AppShell>
      <div className="max-w-4xl mx-auto py-10 px-6 text-slate-300">
        <h1 className="text-3xl font-extrabold text-white mb-6">Terms of Service</h1>
        <p className="text-slate-400 mb-8">Last updated: August 2, 2026</p>

        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4">1. Acceptance of Terms</h2>
          <p className="mb-4">
            By accessing or using our website, you agree to be bound by these Terms of Service. If you do not agree to all of these terms, do not use our services.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4">2. Description of Service</h2>
          <p className="mb-4">
            We provide a job search aggregator and application manager tool. We aggregate listings from public ATS job boards and organic searches. We do not guarantee the availability, accuracy, or authenticity of job postings listed on our platform.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4">3. User Conduct & Acceptable Use</h2>
          <p className="mb-4">
            You agree not to use the service for any unlawful purposes or to conduct any search query spamming. Scraping our system or attempting to disrupt its operation is strictly prohibited.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4">4. Disclaimers & Limitation of Liability</h2>
          <p className="mb-4">
            OUR SERVICES ARE PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT WARRANTIES OF ANY KIND. WE ARE NOT LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING OUT OF YOUR USE OF THE SERVICES.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4">5. Contact Information</h2>
          <p className="mb-4">
            If you have any questions about these Terms of Service, please reach out to us at:
          </p>
          <ul className="list-disc pl-6 text-slate-400">
            <li>Email: nikhilkumaragarwalk@gmail.com</li>
            <li>Phone: +918328051347</li>
          </ul>
        </section>
      </div>
    </AppShell>
  );
}
