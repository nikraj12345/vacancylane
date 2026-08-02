"use client";

import { AppShell } from "@/components/app-shell";
import { Mail, Phone, MapPin } from "lucide-react";

export default function ContactPage() {
  return (
    <AppShell>
      <div className="max-w-4xl mx-auto py-10 px-6 text-slate-300">
        <h1 className="text-3xl font-extrabold text-white mb-6">Contact Us</h1>
        <p className="text-slate-400 mb-8">
          Have questions, feedback, or need assistance? Reach out to us through the channels below. We will get back to you as soon as possible.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md">
            <h2 className="text-xl font-bold text-white mb-6">Contact Information</h2>
            
            <div className="flex items-center gap-4 mb-6">
              <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-lg">
                <Mail className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Email Address</p>
                <a
                  href="mailto:nikhilkumaragarwalk@gmail.com"
                  className="text-white hover:text-indigo-400 font-medium transition"
                >
                  nikhilkumaragarwalk@gmail.com
                </a>
              </div>
            </div>

            <div className="flex items-center gap-4 mb-6">
              <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-lg">
                <Phone className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Phone Number</p>
                <a
                  href="tel:+918328051347"
                  className="text-white hover:text-indigo-400 font-medium transition"
                >
                  +91 8328051347
                </a>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-lg">
                <MapPin className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Location</p>
                <p className="text-white font-medium">India</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md">
            <h2 className="text-xl font-bold text-white mb-4">Send a Message</h2>
            <form onSubmit={(e) => e.preventDefault()} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Your Name</label>
                <input
                  type="text"
                  placeholder="John Doe"
                  className="w-full bg-slate-950 border border-slate-800 text-white rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition"
                  disabled
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Your Email</label>
                <input
                  type="email"
                  placeholder="john@example.com"
                  className="w-full bg-slate-950 border border-slate-800 text-white rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition"
                  disabled
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Message</label>
                <textarea
                  rows={4}
                  placeholder="Hello, I would like to query..."
                  className="w-full bg-slate-950 border border-slate-800 text-white rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition resize-none"
                  disabled
                />
              </div>
              <button
                type="submit"
                className="w-full bg-slate-800 text-slate-500 border border-slate-700 font-medium text-sm py-2.5 rounded-lg cursor-not-allowed"
                disabled
              >
                Inquiries via email or phone only
              </button>
            </form>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
