import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Button,
} from '@fluentui/react-components';
import {
  CalendarIcon,
  MapIcon,
  UsersIcon,
  SparklesIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  GlobeAltIcon,
  HeartIcon,
  ShieldCheckIcon,
  ChevronDownIcon,
  PlayIcon,
} from '@heroicons/react/24/outline';
import { StarIcon as StarSolidIcon } from '@heroicons/react/24/solid';

// Floating elements for hero background
const FloatingElement: React.FC<{ delay: number; size: string; className: string }> = ({
  delay,
  size,
  className,
}) => (
  <motion.div
    className={`absolute rounded-full bg-gradient-to-br opacity-20 blur-xl ${size} ${className}`}
    animate={{
      y: [0, -30, 0],
      x: [0, 15, 0],
      scale: [1, 1.1, 1],
    }}
    transition={{
      duration: 8,
      delay,
      repeat: Infinity,
      ease: 'easeInOut',
    }}
  />
);

// Modern feature card with glassmorphism
const FeatureCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
  gradient: string;
}> = ({ icon, title, description, gradient }) => (
  <motion.div
    whileHover={{ y: -8, scale: 1.02 }}
    transition={{ duration: 0.3, ease: 'easeOut' }}
    className="group relative"
  >
    <div className={`absolute inset-0 rounded-3xl ${gradient} opacity-0 group-hover:opacity-100 blur-xl transition-opacity duration-500`} />
    <div className="relative h-full p-8 rounded-3xl bg-white/80 backdrop-blur-sm border border-gray-100 shadow-lg shadow-gray-100/50 hover:shadow-xl hover:shadow-primary-100/50 transition-all duration-300">
      <div className={`inline-flex p-4 rounded-2xl ${gradient} mb-6`}>
        <div className="text-white">{icon}</div>
      </div>
      <h3 className="text-xl font-bold text-gray-900 mb-3">{title}</h3>
      <p className="text-gray-600 leading-relaxed">{description}</p>
    </div>
  </motion.div>
);

// Step card for "How it works" section
const StepCard: React.FC<{
  number: string;
  title: string;
  description: string;
  icon: React.ReactNode;
}> = ({ number, title, description, icon }) => (
  <motion.div
    initial={{ opacity: 0, y: 30 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    className="relative text-center"
  >
    <div className="relative inline-flex mb-6">
      <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center text-white shadow-lg shadow-primary-200">
        {icon}
      </div>
      <span className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-secondary-500 text-white text-sm font-bold flex items-center justify-center shadow-lg">
        {number}
      </span>
    </div>
    <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
    <p className="text-gray-600">{description}</p>
  </motion.div>
);

// Testimonial card
const TestimonialCard: React.FC<{
  quote: string;
  author: string;
  role: string;
  avatar: string;
  rating: number;
}> = ({ quote, author, role, avatar, rating }) => (
  <motion.div
    whileHover={{ scale: 1.02 }}
    className="p-8 rounded-3xl bg-white shadow-xl shadow-gray-100/50 border border-gray-100"
  >
    <div className="flex gap-1 mb-4">
      {[...Array(5)].map((_, i) => (
        <StarSolidIcon
          key={i}
          className={`w-5 h-5 ${i < rating ? 'text-yellow-400' : 'text-gray-200'}`}
        />
      ))}
    </div>
    <p className="text-gray-700 text-lg leading-relaxed mb-6">"{quote}"</p>
    <div className="flex items-center gap-4">
      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-400 to-secondary-400 flex items-center justify-center text-white font-bold text-lg">
        {avatar}
      </div>
      <div>
        <p className="font-semibold text-gray-900">{author}</p>
        <p className="text-sm text-gray-500">{role}</p>
      </div>
    </div>
  </motion.div>
);

// FAQ Item
const FAQItem: React.FC<{
  question: string;
  answer: string;
  isOpen: boolean;
  onClick: () => void;
}> = ({ question, answer, isOpen, onClick }) => (
  <motion.div
    className="border-b border-gray-100 last:border-0"
    initial={false}
  >
    <button
      onClick={onClick}
      className="w-full py-6 flex items-center justify-between text-left hover:text-primary-600 transition-colors"
    >
      <span className="text-lg font-medium text-gray-900">{question}</span>
      <motion.div
        animate={{ rotate: isOpen ? 180 : 0 }}
        transition={{ duration: 0.2 }}
      >
        <ChevronDownIcon className="w-5 h-5 text-gray-400" />
      </motion.div>
    </button>
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="overflow-hidden"
        >
          <p className="pb-6 text-gray-600 leading-relaxed">{answer}</p>
        </motion.div>
      )}
    </AnimatePresence>
  </motion.div>
);

// Stat card
const StatCard: React.FC<{ value: string; label: string }> = ({ value, label }) => (
  <div className="text-center">
    <motion.p
      initial={{ scale: 0.5, opacity: 0 }}
      whileInView={{ scale: 1, opacity: 1 }}
      viewport={{ once: true }}
      className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-primary-600 to-secondary-500 bg-clip-text text-transparent"
    >
      {value}
    </motion.p>
    <p className="text-gray-600 mt-2">{label}</p>
  </div>
);

export const HomePage: React.FC = () => {
  const { login, isAuthenticated } = useAuth();
  const [openFAQ, setOpenFAQ] = useState<number | null>(0);

  const features = [
    {
      icon: <SparklesIcon className="w-7 h-7" />,
      title: 'AI-Powered Planning',
      description: 'Our intelligent assistant creates personalized itineraries based on your preferences, budget, and travel style.',
      gradient: 'bg-gradient-to-br from-violet-500 to-purple-600',
    },
    {
      icon: <UsersIcon className="w-7 h-7" />,
      title: 'Family Collaboration',
      description: 'Invite family members to collaborate in real-time. Vote on activities, share ideas, and plan together seamlessly.',
      gradient: 'bg-gradient-to-br from-pink-500 to-rose-600',
    },
    {
      icon: <CalendarIcon className="w-7 h-7" />,
      title: 'Smart Scheduling',
      description: 'Automatically optimize your schedule considering travel times, opening hours, and group availability.',
      gradient: 'bg-gradient-to-br from-amber-500 to-orange-600',
    },
    {
      icon: <MapIcon className="w-7 h-7" />,
      title: 'Interactive Maps',
      description: 'Visualize your entire trip with beautiful interactive maps showing routes and points of interest.',
      gradient: 'bg-gradient-to-br from-emerald-500 to-teal-600',
    },
    {
      icon: <HeartIcon className="w-7 h-7" />,
      title: 'Preference Matching',
      description: 'Our AI finds activities that everyone will love by analyzing individual preferences and finding common ground.',
      gradient: 'bg-gradient-to-br from-red-500 to-pink-600',
    },
    {
      icon: <ShieldCheckIcon className="w-7 h-7" />,
      title: 'Secure & Private',
      description: 'Your travel plans and personal data are protected with enterprise-grade security and encryption.',
      gradient: 'bg-gradient-to-br from-blue-500 to-indigo-600',
    },
  ];

  const steps = [
    {
      number: '1',
      title: 'Create Your Trip',
      description: 'Set your destination, dates, and invite family members',
      icon: <GlobeAltIcon className="w-8 h-8" />,
    },
    {
      number: '2',
      title: 'Share Preferences',
      description: 'Everyone adds their interests, must-sees, and budget',
      icon: <HeartIcon className="w-8 h-8" />,
    },
    {
      number: '3',
      title: 'AI Creates Itinerary',
      description: 'Our AI generates the perfect plan that works for everyone',
      icon: <SparklesIcon className="w-8 h-8" />,
    },
    {
      number: '4',
      title: 'Travel & Enjoy',
      description: 'Follow your optimized itinerary and make memories',
      icon: <MapIcon className="w-8 h-8" />,
    },
  ];

  const testimonials = [
    {
      quote: "Pathfinder transformed how our family plans vacations. No more endless group chats and spreadsheets!",
      author: 'Sarah Mitchell',
      role: 'Family of 6, California',
      avatar: 'SM',
      rating: 5,
    },
    {
      quote: "The AI suggestions were spot-on. It found hidden gems we never would have discovered on our own.",
      author: 'James Chen',
      role: 'Adventure Traveler',
      avatar: 'JC',
      rating: 5,
    },
    {
      quote: "Planning a multi-generational trip used to be a nightmare. Pathfinder made it actually enjoyable.",
      author: 'Maria Garcia',
      role: 'Grandmother of 4',
      avatar: 'MG',
      rating: 5,
    },
  ];

  const faqs = [
    {
      question: 'How does the AI create personalized itineraries?',
      answer: 'Our AI analyzes each family member\'s preferences, interests, dietary restrictions, mobility needs, and budget constraints. It then uses advanced algorithms to find activities and restaurants that satisfy everyone while optimizing for travel time and logistics.',
    },
    {
      question: 'Can I invite people who don\'t have an account?',
      answer: 'Yes! You can invite family members via email. They\'ll receive a link to join your trip and can create a free account in seconds. No payment required for basic collaboration features.',
    },
    {
      question: 'What happens if family members have conflicting preferences?',
      answer: 'Pathfinder\'s Magic Polls feature lets your group vote on activities democratically. Our AI also suggests compromises and alternatives that might satisfy multiple preferences at once.',
    },
    {
      question: 'Is my travel data secure?',
      answer: 'Absolutely. We use enterprise-grade encryption, secure Microsoft authentication, and never share your data with third parties. Your travel plans are visible only to people you explicitly invite.',
    },
    {
      question: 'Can I use Pathfinder for solo travel?',
      answer: 'Of course! While Pathfinder shines for group planning, it\'s equally powerful for solo travelers. The AI will create optimized itineraries based on your personal preferences.',
    },
  ];

  return (
    <div className="min-h-screen bg-white overflow-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-lg border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
                <MapIcon className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent">
                Pathfinder
              </span>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-600 hover:text-primary-600 transition-colors">Features</a>
              <a href="#how-it-works" className="text-gray-600 hover:text-primary-600 transition-colors">How It Works</a>
              <a href="#testimonials" className="text-gray-600 hover:text-primary-600 transition-colors">Reviews</a>
              <a href="#faq" className="text-gray-600 hover:text-primary-600 transition-colors">FAQ</a>
            </div>
            <div className="flex items-center gap-3">
              {isAuthenticated ? (
                <Link to="/dashboard">
                  <Button appearance="primary" className="rounded-full px-6">
                    Dashboard
                  </Button>
                </Link>
              ) : (
                <>
                  <button
                    onClick={() => login()}
                    className="text-gray-600 hover:text-primary-600 transition-colors font-medium"
                  >
                    Sign In
                  </button>
                  <Button
                    appearance="primary"
                    className="rounded-full px-6"
                    onClick={() => login()}
                  >
                    Get Started
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 lg:pt-40 lg:pb-32">
        {/* Animated background elements */}
        <div className="absolute inset-0 overflow-hidden">
          <FloatingElement delay={0} size="w-96 h-96" className="from-primary-400 to-primary-600 -top-48 -left-48" />
          <FloatingElement delay={2} size="w-80 h-80" className="from-secondary-400 to-secondary-600 top-1/4 -right-40" />
          <FloatingElement delay={4} size="w-64 h-64" className="from-violet-400 to-purple-600 bottom-0 left-1/4" />
          <FloatingElement delay={1} size="w-72 h-72" className="from-pink-400 to-rose-600 -bottom-20 right-1/4" />
        </div>

        {/* Grid pattern overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#f0f0f0_1px,transparent_1px),linear-gradient(to_bottom,#f0f0f0_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-50 border border-primary-100 text-primary-700 text-sm font-medium mb-8"
            >
              <SparklesIcon className="w-4 h-4" />
              AI-Powered Trip Planning for Families
            </motion.div>

            {/* Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-5xl md:text-6xl lg:text-7xl font-bold text-gray-900 leading-tight mb-6"
            >
              Plan trips that
              <span className="relative">
                <span className="relative z-10 bg-gradient-to-r from-primary-600 via-violet-600 to-secondary-600 bg-clip-text text-transparent"> everyone </span>
                <svg className="absolute -bottom-2 left-0 w-full" viewBox="0 0 200 12" fill="none">
                  <path d="M2 10C50 4 150 4 198 10" stroke="url(#underline-gradient)" strokeWidth="4" strokeLinecap="round"/>
                  <defs>
                    <linearGradient id="underline-gradient" x1="0" y1="0" x2="200" y2="0">
                      <stop stopColor="#2563eb"/>
                      <stop offset="0.5" stopColor="#7c3aed"/>
                      <stop offset="1" stopColor="#16a34a"/>
                    </linearGradient>
                  </defs>
                </svg>
              </span>
              will love
            </motion.h1>

            {/* Subheadline */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-xl text-gray-600 max-w-2xl mx-auto mb-10 leading-relaxed"
            >
              Pathfinder uses AI to understand everyone's preferences and creates the perfect itinerary
              that makes the whole family happy. No more endless debates or compromises.
            </motion.p>

            {/* CTA Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-col sm:flex-row gap-4 justify-center mb-12"
            >
              {isAuthenticated ? (
                <Link to="/dashboard">
                  <button className="group inline-flex items-center gap-2 px-8 py-4 rounded-full bg-gradient-to-r from-primary-600 to-primary-700 text-white font-semibold text-lg shadow-lg shadow-primary-500/30 hover:shadow-xl hover:shadow-primary-500/40 transition-all duration-300">
                    Go to Dashboard
                    <ArrowRightIcon className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </button>
                </Link>
              ) : (
                <>
                  <button
                    onClick={() => login()}
                    className="group inline-flex items-center gap-2 px-8 py-4 rounded-full bg-gradient-to-r from-primary-600 to-primary-700 text-white font-semibold text-lg shadow-lg shadow-primary-500/30 hover:shadow-xl hover:shadow-primary-500/40 transition-all duration-300"
                  >
                    Start Planning Free
                    <ArrowRightIcon className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </button>
                  <button
                    onClick={() => login()}
                    className="group inline-flex items-center gap-2 px-8 py-4 rounded-full bg-white border-2 border-gray-200 text-gray-700 font-semibold text-lg hover:border-primary-300 hover:text-primary-600 transition-all duration-300"
                  >
                    <PlayIcon className="w-5 h-5" />
                    Watch Demo
                  </button>
                </>
              )}
            </motion.div>

            {/* Social Proof */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.5 }}
              className="flex flex-col sm:flex-row items-center justify-center gap-6 text-sm text-gray-500"
            >
              <div className="flex items-center gap-2">
                <div className="flex -space-x-2">
                  {['bg-primary-400', 'bg-secondary-400', 'bg-violet-400', 'bg-pink-400'].map((bg, i) => (
                    <div key={i} className={`w-8 h-8 rounded-full ${bg} border-2 border-white flex items-center justify-center text-white text-xs font-bold`}>
                      {['S', 'J', 'M', 'A'][i]}
                    </div>
                  ))}
                </div>
                <span>Join 10,000+ happy families</span>
              </div>
              <div className="flex items-center gap-1">
                {[...Array(5)].map((_, i) => (
                  <StarSolidIcon key={i} className="w-4 h-4 text-yellow-400" />
                ))}
                <span className="ml-1">4.9/5 rating</span>
              </div>
            </motion.div>
          </div>

          {/* Hero Image/Preview */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.4 }}
            className="mt-16 relative"
          >
            <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-transparent z-10 pointer-events-none" />
            <div className="relative mx-auto max-w-5xl rounded-2xl overflow-hidden shadow-2xl shadow-gray-200 border border-gray-200">
              <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-8 md:p-12">
                <div className="grid md:grid-cols-3 gap-6">
                  {/* Trip Card Preview */}
                  <div className="bg-white rounded-xl p-6 shadow-lg">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
                        <MapIcon className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">Summer in Italy</p>
                        <p className="text-sm text-gray-500">July 15-28, 2026</p>
                      </div>
                    </div>
                    <div className="flex -space-x-2 mb-4">
                      {['bg-blue-400', 'bg-green-400', 'bg-purple-400', 'bg-pink-400'].map((bg, i) => (
                        <div key={i} className={`w-8 h-8 rounded-full ${bg} border-2 border-white`} />
                      ))}
                      <div className="w-8 h-8 rounded-full bg-gray-100 border-2 border-white flex items-center justify-center text-xs text-gray-600 font-medium">+2</div>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <CheckCircleIcon className="w-4 h-4 text-green-500" />
                      <span>AI Itinerary Ready</span>
                    </div>
                  </div>

                  {/* Itinerary Preview */}
                  <div className="bg-white rounded-xl p-6 shadow-lg md:col-span-2">
                    <p className="font-semibold text-gray-900 mb-4">Today's Itinerary</p>
                    <div className="space-y-3">
                      {[
                        { time: '9:00 AM', activity: 'Colosseum Tour', icon: '🏛️' },
                        { time: '12:30 PM', activity: 'Lunch at Trattoria Roma', icon: '🍝' },
                        { time: '3:00 PM', activity: 'Vatican Museums', icon: '🎨' },
                        { time: '7:00 PM', activity: 'Dinner in Trastevere', icon: '🍷' },
                      ].map((item, i) => (
                        <div key={i} className="flex items-center gap-4 p-3 rounded-lg bg-gray-50">
                          <span className="text-2xl">{item.icon}</span>
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">{item.activity}</p>
                            <p className="text-sm text-gray-500">{item.time}</p>
                          </div>
                          <CheckCircleIcon className="w-5 h-5 text-green-500" />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <StatCard value="10K+" label="Happy Families" />
            <StatCard value="50K+" label="Trips Planned" />
            <StatCard value="4.9" label="Average Rating" />
            <StatCard value="98%" label="Satisfaction Rate" />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center max-w-3xl mx-auto mb-16"
          >
            <span className="text-primary-600 font-semibold text-sm uppercase tracking-wider">Features</span>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mt-4 mb-6">
              Everything you need for
              <span className="bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent"> perfect trips</span>
            </h2>
            <p className="text-xl text-gray-600">
              From AI-powered planning to real-time collaboration, Pathfinder has all the tools
              your family needs to plan unforgettable adventures.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <FeatureCard {...feature} />
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-24 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center max-w-3xl mx-auto mb-16"
          >
            <span className="text-primary-600 font-semibold text-sm uppercase tracking-wider">How It Works</span>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mt-4 mb-6">
              Plan your trip in
              <span className="bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent"> 4 simple steps</span>
            </h2>
            <p className="text-xl text-gray-600">
              No complicated setup. No steep learning curve. Just effortless trip planning.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-4 gap-8 relative">
            {/* Connection line */}
            <div className="hidden md:block absolute top-10 left-[12.5%] right-[12.5%] h-0.5 bg-gradient-to-r from-primary-200 via-primary-400 to-primary-200" />

            {steps.map((step, index) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.15 }}
              >
                <StepCard {...step} />
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center max-w-3xl mx-auto mb-16"
          >
            <span className="text-primary-600 font-semibold text-sm uppercase tracking-wider">Testimonials</span>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mt-4 mb-6">
              Loved by
              <span className="bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent"> families worldwide</span>
            </h2>
            <p className="text-xl text-gray-600">
              See what families are saying about their Pathfinder experience.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <motion.div
                key={testimonial.author}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <TestimonialCard {...testimonial} />
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-24 bg-gray-50">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <span className="text-primary-600 font-semibold text-sm uppercase tracking-wider">FAQ</span>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mt-4 mb-6">
              Frequently asked
              <span className="bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent"> questions</span>
            </h2>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="bg-white rounded-2xl p-8 shadow-xl shadow-gray-100/50"
          >
            {faqs.map((faq, index) => (
              <FAQItem
                key={index}
                question={faq.question}
                answer={faq.answer}
                isOpen={openFAQ === index}
                onClick={() => setOpenFAQ(openFAQ === index ? null : index)}
              />
            ))}
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-br from-primary-600 via-violet-600 to-secondary-600 relative overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff_1px,transparent_1px),linear-gradient(to_bottom,#ffffff_1px,transparent_1px)] bg-[size:4rem_4rem]" />
        </div>

        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Ready to plan your next adventure?
            </h2>
            <p className="text-xl text-white/80 mb-10 max-w-2xl mx-auto">
              Join thousands of families who have discovered the joy of stress-free trip planning with Pathfinder.
            </p>
            {!isAuthenticated && (
              <button
                onClick={() => login()}
                className="group inline-flex items-center gap-2 px-10 py-5 rounded-full bg-white text-primary-600 font-bold text-lg shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105"
              >
                Start Planning for Free
                <ArrowRightIcon className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
            )}
            <p className="mt-6 text-white/60 text-sm">
              No credit card required • Free forever for basic features
            </p>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            <div className="md:col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
                  <MapIcon className="w-6 h-6 text-white" />
                </div>
                <span className="text-xl font-bold text-white">Pathfinder</span>
              </div>
              <p className="text-gray-400 max-w-md mb-6">
                AI-powered trip planning that brings families together. Plan unforgettable adventures with ease.
              </p>
              <div className="flex gap-4">
                {['X', 'in', 'f', 'ig'].map((social) => (
                  <a key={social} href="#" className="w-10 h-10 rounded-full bg-gray-800 hover:bg-primary-600 flex items-center justify-center text-gray-400 hover:text-white transition-colors">
                    {social}
                  </a>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Product</h4>
              <ul className="space-y-3">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#faq" className="hover:text-white transition-colors">FAQ</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Company</h4>
              <ul className="space-y-3">
                <li><a href="#" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms of Service</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm">© 2026 Pathfinder. All rights reserved.</p>
            <p className="text-sm flex items-center gap-1">
              Made with <HeartIcon className="w-4 h-4 text-red-500" /> for families everywhere
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};
