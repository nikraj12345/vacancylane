"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AnimatePresence,
  motion,
  useMotionValueEvent,
  useScroll,
  useSpring,
  useTransform,
} from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronDown,
  CircleDot,
  Code2,
  FileSearch,
  FileUp,
  Globe2,
  History,
  Layers3,
  MapPin,
  Radar,
  RotateCcw,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  Upload,
  Users,
  Zap,
} from "lucide-react";

const boards = [
  "Greenhouse",
  "Lever",
  "Ashby",
  "Workday",
  "LinkedIn",
  "Wellfound",
  "Instahyre",
  "SmartRecruiters",
  "Rippling",
  "BambooHR",
];

const searchQueries = [
  "Backend Engineer · Bengaluru",
  "AI Engineer · Remote India",
  "Platform Engineer · Hyderabad",
  "Full Stack · Pune + Delhi",
];

const liveResults = [
  [
    ["Backend Engineer, Search", "Bengaluru, India", "match"],
    ["Software Engineer II", "Bangalore, Karnataka", "match"],
    ["Platform Engineer", "Remote — India", "remote"],
  ],
  [
    ["AI Engineer", "Bengaluru, India", "match"],
    ["ML Platform Engineer", "Hyderabad", "match"],
    ["Applied Scientist", "Remote — India", "remote"],
  ],
  [
    ["Platform Engineer", "Hyderabad, India", "match"],
    ["SRE · Cloud", "Bengaluru", "match"],
    ["Infrastructure Engineer", "Pune", "country"],
  ],
  [
    ["Full Stack Engineer", "Pune, India", "match"],
    ["Frontend Engineer", "Delhi NCR", "match"],
    ["Software Developer", "Remote — India", "remote"],
  ],
] as const;

const features = [
  {
    icon: Radar,
    title: "Search company boards, not aggregators",
    copy: "Query Greenhouse, Lever, Ashby, Workday and more in one pass — where roles appear first.",
  },
  {
    icon: MapPin,
    title: "Location-smart ranking",
    copy: "Exact city matches rise first, same-country roles next, everything else stays visible below.",
  },
  {
    icon: ShieldCheck,
    title: "Fewer closed postings",
    copy: "Live checks drop dead links before they waste a click.",
  },
  {
    icon: FileSearch,
    title: "Search from your resume",
    copy: "Upload a CV and prefill role, skills, experience bands, and locations.",
  },
  {
    icon: CheckCircle2,
    title: "Track every apply",
    copy: "Sign in once, click Apply, and keep a clean history of where you applied.",
  },
  {
    icon: History,
    title: "Replay previous searches",
    copy: "Your past queries stay saved so you can re-run them when new roles drop.",
  },
];

const steps = [
  {
    n: "01",
    title: "Describe the role",
    copy: "Title, skills, experience bands, and one or more locations — or upload a resume to prefill.",
  },
  {
    n: "02",
    title: "Scan live boards",
    copy: "Vacancylane runs ATS-aware queries, ranks what comes back, and flags closed posts.",
  },
  {
    n: "03",
    title: "Apply and track",
    copy: "Open the posting, mark Applied, and keep status updates next to every role.",
  },
];

const personas = [
  {
    icon: Target,
    title: "Focused switchers",
    copy: "You already know the title. You want fresh company-board listings, not recycled aggregator noise.",
  },
  {
    icon: Upload,
    title: "Resume-first hunters",
    copy: "Drop in a CV, get role/skills/location filled, and start scanning boards in under a minute.",
  },
  {
    icon: Users,
    title: "Multi-city candidates",
    copy: "Search Bengaluru, Hyderabad, and Remote together — then sort by how close each role really is.",
  },
];

const trackerPreview = [
  { title: "Backend Engineer", company: "Notion", status: "Applied", tone: "emerald" },
  { title: "Platform Engineer", company: "Stripe", status: "Interview", tone: "amber" },
  { title: "SDE II", company: "Atlassian", status: "Offer", tone: "sky" },
];

const faqs = [
  {
    q: "Which job boards does Vacancylane search?",
    a: "Company career systems like Greenhouse, Lever, Ashby, Workday, and several others — the places roles usually appear before aggregators catch up.",
  },
  {
    q: "Do I need an account to search?",
    a: "No. Search works without signing in. Create a free account when you want application tracking and saved search history.",
  },
  {
    q: "How does resume search work?",
    a: "Upload a PDF, DOCX, or text resume. Vacancylane extracts role, skills, experience band, and location hints and prefills the search form — no LLM required.",
  },
  {
    q: "Are the postings verified?",
    a: "When live checks are on, Vacancylane probes listing pages and drops clearly closed or broken links before they clutter your results.",
  },
];

const floatingTags = [
  {
    icon: Code2,
    label: "Senior Backend Engineer",
    meta: "Bengaluru",
    className: "-left-40 top-30",
    delay: 0,
  },
  {
    icon: Globe2,
    label: "Remote · India",
    meta: "142 roles",
    className: "-right-14 top-28",
    delay: 0.8,
  },
  {
    icon: Layers3,
    label: "Platform Engineer",
    meta: "92% match",
    className: "-left-20 bottom-20",
    delay: 1.5,
  },
];

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  show: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: {
      delay: i * 0.08,
      duration: 0.55,
      ease: [0.22, 1, 0.36, 1] as const,
    },
  }),
};

const stagger = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.08, delayChildren: 0.05 },
  },
};

const item = {
  hidden: { opacity: 0, y: 22 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] as const },
  },
};

function FloatingTag({
  icon: Icon,
  label,
  meta,
  className,
  delay,
}: (typeof floatingTags)[number]) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{
        opacity: 1,
        scale: 1,
        y: [0, -10, 0],
        rotate: [0, 1.5, 0],
      }}
      transition={{
        opacity: { delay: 0.8 + delay * 0.1, duration: 0.5 },
        scale: { delay: 0.8 + delay * 0.1, duration: 0.5 },
        y: { delay, duration: 4.5, repeat: Infinity, ease: "easeInOut" },
        rotate: { delay, duration: 5.5, repeat: Infinity, ease: "easeInOut" },
      }}
      className={`absolute z-20 hidden items-center gap-3 rounded-2xl border border-white/10 bg-[#111714]/85 px-3.5 py-3 shadow-2xl shadow-black/40 backdrop-blur-xl xl:flex ${className}`}
    >
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-400/12 text-emerald-300">
        <Icon className="h-4 w-4" />
      </span>
      <span>
        <span className="block whitespace-nowrap text-xs font-semibold text-slate-100">
          {label}
        </span>
        <span className="mt-0.5 block text-[10px] text-slate-500">{meta}</span>
      </span>
    </motion.div>
  );
}

function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 120,
    damping: 28,
    restDelta: 0.001,
  });

  return (
    <motion.div
      style={{ scaleX }}
      className="fixed left-0 right-0 top-0 z-50 h-[2px] origin-left bg-gradient-to-r from-emerald-400 via-teal-300 to-lime-300"
    />
  );
}

function AnimatedCount({ value, suffix = "" }: { value: number; suffix?: string }) {
  const [display, setDisplay] = useState(0);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    if (!started) return;
    let frame = 0;
    const total = 36;
    const id = window.setInterval(() => {
      frame += 1;
      const next = Math.round((value * frame) / total);
      setDisplay(next);
      if (frame >= total) window.clearInterval(id);
    }, 28);
    return () => window.clearInterval(id);
  }, [started, value]);

  return (
    <motion.span
      onViewportEnter={() => setStarted(true)}
      viewport={{ once: true }}
    >
      {display}
      {suffix}
    </motion.span>
  );
}

function FaqItem({
  q,
  a,
  open,
  onToggle,
}: {
  q: string;
  a: string;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <motion.div
      variants={item}
      className="overflow-hidden rounded-2xl border border-white/8 bg-white/[0.02]"
    >
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
      >
        <span className="text-sm font-medium text-slate-100 sm:text-base">{q}</span>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.25 }}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/8 text-slate-400"
        >
          <ChevronDown className="h-4 w-4" />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
          >
            <p className="px-5 pb-5 text-sm leading-6 text-slate-500">{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function LandingPage() {
  const [queryIndex, setQueryIndex] = useState(0);
  const [openFaq, setOpenFaq] = useState<number | null>(0);
  const { scrollY } = useScroll();
  const [navSolid, setNavSolid] = useState(false);
  const heroY = useTransform(scrollY, [0, 420], [0, 80]);
  const heroOpacity = useTransform(scrollY, [0, 380], [1, 0.35]);

  useMotionValueEvent(scrollY, "change", (value) => {
    setNavSolid(value > 24);
  });

  useEffect(() => {
    const id = window.setInterval(() => {
      setQueryIndex((current) => (current + 1) % searchQueries.length);
    }, 3200);
    return () => window.clearInterval(id);
  }, []);

  const activeResults = liveResults[queryIndex];

  return (
    <main className="landing-page relative min-h-screen overflow-hidden bg-[#080a09] text-white">
      <ScrollProgress />
      <div className="landing-grid pointer-events-none fixed inset-0 opacity-35" />
      <div className="landing-noise pointer-events-none fixed inset-0" />
      <div className="landing-stars pointer-events-none fixed inset-0" />
      <div className="landing-orb landing-orb-one" />
      <div className="landing-orb landing-orb-two" />
      <div className="landing-orb landing-orb-three" />

      <motion.nav
        animate={{
          backgroundColor: navSolid ? "rgba(8,10,9,0.88)" : "rgba(8,10,9,0.55)",
          borderColor: navSolid ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.04)",
        }}
        className="sticky top-0 z-40 mx-auto flex h-20 max-w-7xl items-center justify-between border-b px-5 backdrop-blur-2xl sm:px-8"
      >
        <Link href="/" className="flex items-center gap-3">
          <motion.span
            initial={{ scale: 0.7, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            whileHover={{ rotate: -8, scale: 1.05 }}
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-300/20 bg-emerald-400 text-[#07100c] shadow-lg shadow-emerald-950/40"
          >
            <BriefcaseBusiness className="h-5 w-5" />
          </motion.span>
          <span className="font-[family-name:var(--font-display)] text-lg font-semibold tracking-tight">
            Vacancylane
          </span>
        </Link>
        <div className="flex items-center gap-2">
          <Link
            href="#features"
            className="hidden rounded-lg px-3 py-2 text-sm text-slate-400 transition hover:text-white md:inline-flex"
          >
            Features
          </Link>
          <Link
            href="#how"
            className="hidden rounded-lg px-3 py-2 text-sm text-slate-400 transition hover:text-white md:inline-flex"
          >
            How it works
          </Link>
          <Link
            href="/search"
            className="hidden rounded-lg px-4 py-2 text-sm text-slate-400 transition hover:text-white sm:inline-flex"
          >
            Search
          </Link>
          <Link
            href="/login"
            className="rounded-lg px-4 py-2 text-sm text-slate-300 transition hover:bg-white/5 hover:text-white"
          >
            Sign in
          </Link>
          <motion.div whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }}>
            <Link
              href="/signup"
              className="landing-cta rounded-xl bg-emerald-400 px-4 py-2 text-sm font-semibold text-[#07100c] shadow-lg shadow-emerald-950/30 transition hover:bg-emerald-300"
            >
              Get started
            </Link>
          </motion.div>
        </div>
      </motion.nav>

      <motion.section
        style={{ y: heroY, opacity: heroOpacity }}
        className="relative z-10 mx-auto grid min-h-[calc(100vh-5rem)] max-w-7xl items-center gap-14 px-5 pb-24 pt-14 sm:px-8 lg:grid-cols-[1.02fr_.98fr] lg:pb-28 lg:pt-12"
      >
        <div>
          <motion.div
            custom={0}
            variants={fadeUp}
            initial="hidden"
            animate="show"
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/8 px-3 py-1.5 text-xs text-emerald-200"
          >
            <motion.span
              animate={{ rotate: [0, 15, -10, 0] }}
              transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
            >
              <Sparkles className="h-3.5 w-3.5" />
            </motion.span>
            Live openings from company career pages
          </motion.div>
          <motion.p
            custom={0.5}
            variants={fadeUp}
            initial="hidden"
            animate="show"
            className="mb-3 font-[family-name:var(--font-display)] text-sm font-semibold tracking-[0.18em] text-emerald-300/90 uppercase"
          >
            Vacancylane
          </motion.p>
          <motion.h1
            custom={1}
            variants={fadeUp}
            initial="hidden"
            animate="show"
            className="max-w-3xl font-[family-name:var(--font-display)] text-5xl font-semibold leading-[.98] tracking-[-0.055em] sm:text-6xl lg:text-[5.15rem]"
          >
            Stop scrolling.
            <span className="landing-gradient-text mt-2 block">
              Start finding.
            </span>
          </motion.h1>
          <motion.p
            custom={2}
            variants={fadeUp}
            initial="hidden"
            animate="show"
            className="mt-6 max-w-xl text-base leading-7 text-slate-400 sm:text-lg"
          >
            Search live roles across the web&apos;s best hiring platforms in one
            place. Vacancylane ranks the right openings, removes dead ends, and
            keeps your entire job hunt moving.
          </motion.p>
          <motion.div
            custom={3}
            variants={fadeUp}
            initial="hidden"
            animate="show"
            className="mt-9 flex flex-wrap items-center gap-3"
          >
            <motion.div whileHover={{ y: -4 }} whileTap={{ scale: 0.98 }}>
              <Link
                href="/search"
                className="landing-cta group inline-flex h-12 items-center gap-2 rounded-xl bg-emerald-400 px-6 text-sm font-semibold text-[#07100c] shadow-xl shadow-emerald-950/40 transition hover:bg-emerald-300 hover:shadow-emerald-900/50"
              >
                Start searching
                <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
              </Link>
            </motion.div>
            <motion.div whileHover={{ y: -3 }} whileTap={{ scale: 0.98 }}>
              <Link
                href="/signup"
                className="inline-flex h-12 items-center rounded-xl border border-white/10 bg-white/[0.04] px-6 text-sm font-medium text-slate-200 backdrop-blur transition hover:bg-white/[0.08]"
              >
                Create free account
              </Link>
            </motion.div>
          </motion.div>
          <motion.div
            custom={4}
            variants={fadeUp}
            initial="hidden"
            animate="show"
            className="mt-8 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-500"
          >
            {["Free to start", "Google sign-in", "Application tracker"].map(
              (entry, index) => (
                <motion.span
                  key={entry}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.55 + index * 0.1 }}
                  className="inline-flex items-center gap-1.5"
                >
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  {entry}
                </motion.span>
              )
            )}
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.25, duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="relative mx-auto w-full max-w-xl lg:translate-x-3"
        >
          <div className="landing-radar absolute left-1/2 top-1/2 h-[38rem] w-[38rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-emerald-400/[0.06]" />
          <div className="landing-radar landing-radar-delay absolute left-1/2 top-1/2 h-[28rem] w-[28rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-emerald-400/[0.08]" />
          {floatingTags.map((tag) => (
            <FloatingTag key={tag.label} {...tag} />
          ))}
          <div className="landing-card-glow absolute -inset-12 rounded-[4rem] bg-emerald-400/12 blur-3xl" />
          <motion.div
            animate={{ y: [0, -7, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
            className="relative overflow-hidden rounded-[1.75rem] border border-white/10 bg-[#0d100e]/92 p-4 shadow-2xl shadow-black/60 backdrop-blur-xl sm:p-6"
          >
            <div className="landing-scan-line pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-300 to-transparent" />
            <div className="mb-5 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-rose-400/80" />
                <span className="h-2.5 w-2.5 rounded-full bg-amber-400/80" />
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/80" />
              </div>
              <span className="inline-flex items-center gap-1.5 text-[10px] uppercase tracking-[0.2em] text-slate-600">
                <motion.span
                  animate={{ scale: [1, 1.25, 1], opacity: [0.7, 1, 0.7] }}
                  transition={{ duration: 1.6, repeat: Infinity }}
                >
                  <Zap className="h-3 w-3 text-emerald-400" />
                </motion.span>
                Scanning live
              </span>
            </div>
            <div className="rounded-2xl border border-white/8 bg-white/[0.035] p-4">
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <Search className="h-4 w-4 shrink-0 text-emerald-400" />
                <div className="relative h-5 min-w-0 flex-1 overflow-hidden">
                  <AnimatePresence mode="wait">
                    <motion.span
                      key={searchQueries[queryIndex]}
                      initial={{ y: 14, opacity: 0 }}
                      animate={{ y: 0, opacity: 1 }}
                      exit={{ y: -14, opacity: 0 }}
                      transition={{ duration: 0.35 }}
                      className="absolute inset-0 truncate"
                    >
                      {searchQueries[queryIndex]}
                    </motion.span>
                  </AnimatePresence>
                </div>
                <span className="landing-caret h-4 w-px bg-emerald-400" />
              </div>
            </div>
            <div className="mt-4 space-y-3">
              <AnimatePresence mode="wait">
                <motion.div
                  key={queryIndex}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.25 }}
                  className="space-y-3"
                >
                  {activeResults.map(([title, location, tag], index) => (
                    <motion.div
                      key={title}
                      initial={{ opacity: 0, x: 18 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1, duration: 0.4 }}
                      whileHover={{
                        x: 5,
                        backgroundColor: "rgba(255,255,255,.05)",
                      }}
                      className="flex items-center gap-4 rounded-2xl border border-white/8 bg-white/[0.025] p-4"
                    >
                      <motion.span
                        animate={{
                          boxShadow: [
                            "0 0 0 0 rgba(52,211,153,0)",
                            "0 0 0 6px rgba(52,211,153,0.08)",
                            "0 0 0 0 rgba(52,211,153,0)",
                          ],
                        }}
                        transition={{
                          duration: 2.8,
                          repeat: Infinity,
                          delay: index * 0.4,
                        }}
                        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-slate-700 to-slate-900 text-xs font-bold text-slate-300"
                      >
                        {title.slice(0, 1)}
                      </motion.span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-slate-100">
                          {title}
                        </p>
                        <p className="mt-1 flex items-center gap-1 text-xs text-slate-500">
                          <MapPin className="h-3 w-3" />
                          {location}
                        </p>
                      </div>
                      <span className="rounded-lg border border-emerald-400/20 bg-emerald-500/10 px-2 py-1 text-[10px] font-semibold text-emerald-300">
                        {tag}
                      </span>
                    </motion.div>
                  ))}
                </motion.div>
              </AnimatePresence>
            </div>
            <div className="mt-5 flex items-center justify-between border-t border-white/[0.06] pt-4">
              <div className="flex items-center gap-2 text-[11px] text-slate-500">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-50" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
                </span>
                11 sources connected
              </div>
              <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-300">
                <AnimatedCount value={247} /> live roles
                <TrendingUp className="h-3 w-3" />
              </span>
            </div>
          </motion.div>
        </motion.div>
      </motion.section>

      <section className="relative z-10 mx-auto -mt-6 grid max-w-7xl grid-cols-2 gap-px overflow-hidden rounded-2xl border border-white/[0.06] bg-white/[0.06] sm:grid-cols-4">
        {[
          { value: <AnimatedCount value={11} suffix="+" />, label: "job sources", Icon: Globe2 },
          { value: "Live", label: "posting checks", Icon: CircleDot },
          { value: "Smart", label: "location ranking", Icon: BarChart3 },
          { value: "One", label: "application hub", Icon: CheckCircle2 },
        ].map(({ value, label, Icon }, index) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.08 }}
            whileHover={{ y: -3 }}
            className="group bg-[#0b0e0c] px-5 py-6 text-center transition hover:bg-emerald-400/[0.04]"
          >
            <Icon className="mx-auto mb-3 h-4 w-4 text-emerald-400 transition group-hover:scale-125" />
            <p className="text-xl font-semibold text-white">{value}</p>
            <p className="mt-1 text-xs text-slate-600">{label}</p>
          </motion.div>
        ))}
      </section>

      <section className="relative z-10 border-y border-white/[0.06] bg-white/[0.018]">
        <div className="mx-auto max-w-7xl overflow-hidden px-5 py-8 sm:px-8">
          <p className="mb-5 text-center text-[10px] font-semibold uppercase tracking-[0.25em] text-slate-600">
            One search across the systems companies actually use
          </p>
          <div className="landing-marquee flex w-max gap-5">
            {[...boards, ...boards].map((board, i) => (
              <motion.span
                key={`${board}-${i}`}
                whileHover={{ y: -3, color: "#a7f3d0" }}
                className="flex items-center gap-2 rounded-full border border-white/[0.06] bg-white/[0.025] px-5 py-2.5 text-sm font-medium text-slate-400"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400/70" />
                {board}
              </motion.span>
            ))}
          </div>
          <div className="landing-marquee landing-marquee-reverse mt-4 flex w-max gap-5">
            {[...boards].reverse().concat([...boards].reverse()).map((board, i) => (
              <span
                key={`rev-${board}-${i}`}
                className="flex items-center gap-2 rounded-full border border-emerald-400/10 bg-emerald-400/[0.04] px-5 py-2.5 text-sm font-medium text-slate-500"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-teal-400/60" />
                {board}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section id="features" className="relative z-10 mx-auto max-w-7xl px-5 py-24 sm:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
          className="max-w-2xl"
        >
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">
            Why Vacancylane
          </p>
          <h2 className="mt-3 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight sm:text-4xl">
            Built for focused searching, not endless scrolling.
          </h2>
        </motion.div>
        <motion.div
          variants={stagger}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-40px" }}
          className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
        >
          {features.map(({ icon: Icon, title, copy }, index) => (
            <motion.div
              key={title}
              variants={item}
              whileHover={{ y: -8, rotateX: 2, rotateY: index % 2 ? 2 : -2 }}
              className="landing-feature-card group relative overflow-hidden rounded-2xl border border-white/8 bg-white/[0.025] p-5"
            >
              <div className="absolute -right-16 -top-16 h-32 w-32 rounded-full bg-emerald-400/0 blur-3xl transition duration-500 group-hover:bg-emerald-400/15" />
              <motion.span
                whileHover={{ rotate: -8, scale: 1.08 }}
                className="mb-5 flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-400/15 bg-emerald-400/8 text-emerald-300"
              >
                <Icon className="h-5 w-5" />
              </motion.span>
              <h3 className="font-semibold text-slate-100">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">{copy}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <section className="relative z-10 border-y border-white/[0.06] bg-[#0b0e0c]/80">
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-5 py-24 sm:px-8 lg:grid-cols-2">
          <motion.div
            initial={{ opacity: 0, x: -24 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55 }}
          >
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">
              Resume search
            </p>
            <h2 className="mt-3 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight sm:text-4xl">
              Drop your CV. Prefill the hunt.
            </h2>
            <p className="mt-4 max-w-lg text-sm leading-7 text-slate-500 sm:text-base">
              Upload a PDF or DOCX and Vacancylane reads role, skills, experience,
              and location hints — then drops them straight into the search form.
            </p>
            <ul className="mt-8 space-y-3">
              {[
                "Role + alternate titles from your header",
                "Skills pulled from your stack section",
                "Experience band inferred from dates",
              ].map((line, index) => (
                <motion.li
                  key={line}
                  initial={{ opacity: 0, x: -12 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.1 + index * 0.08 }}
                  className="flex items-start gap-3 text-sm text-slate-300"
                >
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-400/15 text-emerald-300">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                  </span>
                  {line}
                </motion.li>
              ))}
            </ul>
            <motion.div className="mt-8" whileHover={{ y: -3 }}>
              <Link
                href="/search"
                className="inline-flex h-11 items-center gap-2 rounded-xl bg-emerald-400 px-5 text-sm font-semibold text-[#07100c] transition hover:bg-emerald-300"
              >
                Try resume search
                <FileUp className="h-4 w-4" />
              </Link>
            </motion.div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 28, rotate: 2 }}
            whileInView={{ opacity: 1, x: 0, rotate: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="relative"
          >
            <div className="landing-card-glow absolute -inset-8 rounded-[3rem] bg-teal-400/10 blur-3xl" />
            <motion.div
              animate={{ y: [0, -6, 0] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
              className="relative overflow-hidden rounded-3xl border border-white/10 bg-[#0d100e] p-6 shadow-2xl"
            >
              <div className="flex items-center justify-between">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-600">
                  Resume parse
                </p>
                <motion.span
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="text-[10px] font-medium text-emerald-300"
                >
                  Ready
                </motion.span>
              </div>
              <motion.div
                whileHover={{ scale: 1.01 }}
                className="mt-5 flex flex-col items-center justify-center rounded-2xl border border-dashed border-emerald-400/25 bg-emerald-400/[0.04] px-6 py-10 text-center"
              >
                <motion.span
                  animate={{ y: [0, -4, 0] }}
                  transition={{ duration: 2.2, repeat: Infinity }}
                  className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-400/15 text-emerald-300"
                >
                  <Upload className="h-5 w-5" />
                </motion.span>
                <p className="mt-4 text-sm font-medium text-slate-200">
                  resume_backend.pdf
                </p>
                <p className="mt-1 text-xs text-slate-500">Drop or browse to parse</p>
              </motion.div>
              <div className="mt-5 grid gap-2">
                {[
                  ["Role", "Backend Engineer"],
                  ["Skills", "Python, FastAPI, Kafka"],
                  ["Experience", "5–8 years"],
                  ["Location", "Bengaluru"],
                ].map(([label, value], index) => (
                  <motion.div
                    key={label}
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.15 + index * 0.08 }}
                    className="flex items-center justify-between rounded-xl border border-white/6 bg-white/[0.02] px-3 py-2.5 text-xs"
                  >
                    <span className="text-slate-500">{label}</span>
                    <span className="font-medium text-slate-200">{value}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      <section id="how" className="relative z-10 mx-auto max-w-7xl px-5 py-24 sm:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-2xl"
        >
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">
            How it works
          </p>
          <h2 className="mt-3 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight sm:text-4xl">
            Three steps from search to tracked apply.
          </h2>
        </motion.div>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {steps.map((step, index) => (
            <motion.div
              key={step.n}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -5 }}
              className="group relative overflow-hidden rounded-2xl border border-white/8 bg-white/[0.015] p-6"
            >
              {index < steps.length - 1 && (
                <motion.span
                  initial={{ scaleX: 0 }}
                  whileInView={{ scaleX: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.35 + index * 0.1, duration: 0.7 }}
                  className="absolute right-[-1.6rem] top-12 z-20 hidden h-px w-7 origin-left bg-gradient-to-r from-emerald-400 to-emerald-400/10 md:block"
                />
              )}
              <motion.span
                initial={{ opacity: 0.15, y: 8 }}
                whileInView={{ opacity: 0.25, y: 0 }}
                viewport={{ once: true }}
                className="font-[family-name:var(--font-display)] text-4xl font-semibold text-emerald-400/25"
              >
                {step.n}
              </motion.span>
              <h3 className="mt-4 text-lg font-semibold text-white">{step.title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">{step.copy}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="relative z-10 border-y border-white/[0.06] bg-white/[0.015]">
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-5 py-24 sm:px-8 lg:grid-cols-2">
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="relative order-2 lg:order-1"
          >
            <div className="landing-card-glow absolute -inset-8 rounded-[3rem] bg-emerald-400/10 blur-3xl" />
            <div className="relative space-y-3">
              {trackerPreview.map((row, index) => (
                <motion.div
                  key={row.title}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.12 }}
                  whileHover={{ x: 6 }}
                  className="flex items-center justify-between rounded-2xl border border-white/8 bg-[#0d100e] px-4 py-4"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-100">{row.title}</p>
                    <p className="mt-1 text-xs text-slate-500">{row.company}</p>
                  </div>
                  <motion.span
                    animate={{ scale: [1, 1.04, 1] }}
                    transition={{
                      duration: 2.4,
                      repeat: Infinity,
                      delay: index * 0.35,
                    }}
                    className={
                      row.tone === "amber"
                        ? "rounded-lg border border-amber-400/20 bg-amber-400/10 px-2.5 py-1 text-[10px] font-semibold text-amber-200"
                        : row.tone === "sky"
                          ? "rounded-lg border border-sky-400/20 bg-sky-400/10 px-2.5 py-1 text-[10px] font-semibold text-sky-200"
                          : "rounded-lg border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-[10px] font-semibold text-emerald-300"
                    }
                  >
                    {row.status}
                  </motion.span>
                </motion.div>
              ))}
              <motion.div
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                className="flex items-center gap-2 rounded-2xl border border-dashed border-white/10 px-4 py-3 text-xs text-slate-500"
              >
                <RotateCcw className="h-3.5 w-3.5 text-emerald-400" />
                Re-run any past search from History in one click
              </motion.div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 24 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="order-1 lg:order-2"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">
              Stay organized
            </p>
            <h2 className="mt-3 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight sm:text-4xl">
              Applications and history, side by side.
            </h2>
            <p className="mt-4 max-w-lg text-sm leading-7 text-slate-500 sm:text-base">
              Mark Applied from any result, update status as interviews move, and
              replay yesterday&apos;s search when new roles land overnight.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/applications"
                className="inline-flex h-11 items-center gap-2 rounded-xl border border-white/12 bg-white/[0.04] px-5 text-sm font-medium transition hover:bg-white/[0.08]"
              >
                Open tracker
              </Link>
              <Link
                href="/history"
                className="inline-flex h-11 items-center gap-2 rounded-xl border border-white/12 bg-white/[0.04] px-5 text-sm font-medium transition hover:bg-white/[0.08]"
              >
                View history
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="relative z-10 mx-auto max-w-7xl px-5 py-24 sm:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mx-auto max-w-2xl text-center"
        >
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">
            Who it&apos;s for
          </p>
          <h2 className="mt-3 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight sm:text-4xl">
            Built around how people actually hunt.
          </h2>
        </motion.div>
        <motion.div
          variants={stagger}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="mt-12 grid gap-4 md:grid-cols-3"
        >
          {personas.map(({ icon: Icon, title, copy }) => (
            <motion.div
              key={title}
              variants={item}
              whileHover={{ y: -6 }}
              className="rounded-2xl border border-white/8 bg-gradient-to-b from-white/[0.04] to-transparent p-6"
            >
              <span className="flex h-11 w-11 items-center justify-center rounded-xl border border-emerald-400/15 bg-emerald-400/8 text-emerald-300">
                <Icon className="h-5 w-5" />
              </span>
              <h3 className="mt-5 text-lg font-semibold text-white">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">{copy}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <section className="relative z-10 border-y border-white/[0.06] bg-[#0b0e0c]/70">
        <div className="mx-auto max-w-3xl px-5 py-24 sm:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">
              FAQ
            </p>
            <h2 className="mt-3 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight sm:text-4xl">
              Quick answers before you dive in.
            </h2>
          </motion.div>
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="mt-10 space-y-3"
          >
            {faqs.map((faq, index) => (
              <FaqItem
                key={faq.q}
                q={faq.q}
                a={faq.a}
                open={openFaq === index}
                onToggle={() =>
                  setOpenFaq((current) => (current === index ? null : index))
                }
              />
            ))}
          </motion.div>
        </div>
      </section>

      <section className="relative z-10 mx-auto max-w-7xl px-5 py-24 sm:px-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="relative overflow-hidden rounded-3xl border border-emerald-400/20 bg-gradient-to-br from-emerald-500/12 via-[#0d100e] to-teal-500/8 p-8 sm:p-12"
        >
          <div className="landing-card-glow absolute inset-0 opacity-40" />
          <div className="landing-cta-ring absolute -right-24 -top-24 h-80 w-80 rounded-full border border-emerald-300/10" />
          <div className="landing-cta-ring landing-cta-ring-two absolute -right-12 -top-12 h-56 w-56 rounded-full border border-emerald-300/10" />
          <motion.div
            animate={{ x: [0, 12, 0], y: [0, -8, 0] }}
            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
            className="pointer-events-none absolute bottom-8 left-8 h-24 w-24 rounded-full bg-emerald-400/10 blur-2xl"
          />
          <div className="relative max-w-2xl">
            <h2 className="font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight sm:text-4xl">
              Ready to search smarter?
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-400 sm:text-base">
              Jump into live ATS search, or create an account to track applies and
              save your previous queries.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <motion.div whileHover={{ y: -3 }} whileTap={{ scale: 0.98 }}>
                <Link
                  href="/search"
                  className="landing-cta inline-flex h-11 items-center gap-2 rounded-xl bg-emerald-400 px-5 text-sm font-semibold text-[#07100c] transition hover:bg-emerald-300"
                >
                  Open search
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </motion.div>
              <motion.div whileHover={{ y: -3 }} whileTap={{ scale: 0.98 }}>
                <Link
                  href="/signup"
                  className="inline-flex h-11 items-center rounded-xl border border-white/15 bg-white/[0.04] px-5 text-sm font-medium transition hover:bg-white/[0.08]"
                >
                  Sign up free
                </Link>
              </motion.div>
            </div>
          </div>
        </motion.div>
      </section>

      <footer className="relative z-10 border-t border-white/[0.06]">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-8 text-xs text-slate-600 sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <span>© 2026 Vacancylane</span>
          <div className="flex flex-wrap gap-4">
            <Link href="/search" className="transition hover:text-slate-400">
              Search
            </Link>
            <Link href="/applications" className="transition hover:text-slate-400">
              Applied
            </Link>
            <Link href="/history" className="transition hover:text-slate-400">
              History
            </Link>
            <Link href="#features" className="transition hover:text-slate-400">
              Features
            </Link>
            <Link href="#how" className="transition hover:text-slate-400">
              How it works
            </Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
