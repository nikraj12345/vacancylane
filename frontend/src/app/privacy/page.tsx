"use client";

import { AppShell } from "@/components/app-shell";

export default function PrivacyPage() {
  return (
    <AppShell>
      <div className="max-w-4xl mx-auto py-10 px-6 text-slate-300">
        <h1 className="text-3xl font-extrabold text-white mb-6">Privacy Policy</h1>
        <p className="text-slate-400 mb-8">Last updated: August 2, 2026</p>

        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4">1. Information We Collect</h2>
          <p className="mb-4">
            We collect information you provide directly to us when using our services. This includes search queries, selected filters, and other history items you save while using our search tool.
          </p>
          <p className="mb-4">
            If you log in using Google Auth, we retrieve your email address, name, and profile picture URL as provided by Google&apos;s OAuth service to create and manage your profile.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4">2. How We Use Information</h2>
          <p className="mb-4">
            We use the information we collect to operate, maintain, and improve our services, including to store your search history, keep track of job applications, and personalize your experience.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4">3. Google AdSense & Cookies</h2>
          <p className="mb-4">
            We may use Google AdSense to serve advertisements on our site. Google uses cookies to serve ads based on your prior visits to our website or other websites. Google&apos;s use of advertising cookies enables it and its partners to serve ads based on your visit to our sites and/or other sites on the Internet.
          </p>
          <p className="mb-4">
            Users may opt out of personalized advertising by visiting{" "}
            <a
              href="https://www.google.com/settings/ads"
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-400 hover:underline"
            >
              Google Ads Settings
            </a>.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4">4. Security</h2>
          <p className="mb-4">
            We take reasonable measures to protect your personal information from loss, theft, misuse, and unauthorized access, disclosure, alteration, and destruction.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4">5. Contact Us</h2>
          <p className="mb-4">
            If you have any questions about this Privacy Policy, please contact us at:
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
