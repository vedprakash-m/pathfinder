import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { motion } from 'framer-motion';
import {
  Card,
  CardHeader,
  CardContent,
  Button,
  Title1,
  Title2,
  Body1,
  Body2,
} from '@fluentui/react-components';
import {
  CalendarIcon,
  MapIcon,
  UsersIcon,
  SparkleIcon,
} from '@heroicons/react/24/outline';

const FeatureCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
}> = ({ icon, title, description }) => (
  <motion.div
    whileHover={{ y: -4 }}
    transition={{ duration: 0.2 }}
  >
    <Card className="h-full border-2 border-transparent hover:border-primary-100 transition-colors">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-50 rounded-lg text-primary-600">
            {icon}
          </div>
          <Title2 className="text-neutral-900">{title}</Title2>
        </div>
      </CardHeader>
      <CardContent>
        <Body1 className="text-neutral-600">{description}</Body1>
      </CardContent>
    </Card>
  </motion.div>
);

export const HomePage: React.FC = () => {
  const { loginWithRedirect, isAuthenticated } = useAuth0();

  const features = [
    {
      icon: <SparkleIcon className="w-6 h-6" />,
      title: "AI-Powered Planning",
      description: "Let our intelligent assistant help you create the perfect itinerary based on your preferences and budget."
    },
    {
      icon: <UsersIcon className="w-6 h-6" />,
      title: "Family Collaboration",
      description: "Plan trips together with family members, share ideas, and vote on activities in real-time."
    },
    {
      icon: <CalendarIcon className="w-6 h-6" />,
      title: "Smart Scheduling",
      description: "Automatically optimize your schedule with travel times, opening hours, and availability."
    },
    {
      icon: <MapIcon className="w-6 h-6" />,
      title: "Interactive Maps",
      description: "Visualize your trip with beautiful maps showing routes, attractions, and recommendations."
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <Title1 className="text-5xl md:text-6xl font-bold text-neutral-900 mb-6">
              Plan Perfect Trips with
              <span className="text-primary-600 block">AI Intelligence</span>
            </Title1>
            <Body1 className="text-xl text-neutral-600 max-w-3xl mx-auto mb-8">
              Pathfinder uses advanced AI to help families plan unforgettable trips together. 
              From destination research to itinerary optimization, we make trip planning effortless.
            </Body1>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              {isAuthenticated ? (
                <Link to="/dashboard">
                  <Button appearance="primary" size="large" className="px-8 py-3">
                    Go to Dashboard
                  </Button>
                </Link>
              ) : (
                <>
                  <Button
                    appearance="primary"
                    size="large"
                    className="px-8 py-3"
                    onClick={() => loginWithRedirect()}
                  >
                    Get Started Free
                  </Button>
                  <Button
                    appearance="outline"
                    size="large"
                    className="px-8 py-3"
                    onClick={() => loginWithRedirect({ screen_hint: 'signin' })}
                  >
                    Sign In
                  </Button>
                </>
              )}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <Title1 className="text-4xl font-bold text-neutral-900 mb-4">
              Why Choose Pathfinder?
            </Title1>
            <Body1 className="text-xl text-neutral-600 max-w-2xl mx-auto">
              Experience the future of trip planning with features designed for modern families.
            </Body1>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <FeatureCard {...feature} />
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-r from-primary-600 to-secondary-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <Title1 className="text-4xl font-bold text-white mb-6">
              Ready to Start Planning?
            </Title1>
            <Body1 className="text-xl text-primary-100 mb-8">
              Join thousands of families who trust Pathfinder for their travel planning needs.
            </Body1>
            {!isAuthenticated && (
              <Button
                appearance="primary"
                size="large"
                className="px-8 py-3 bg-white text-primary-600 hover:bg-primary-50"
                onClick={() => loginWithRedirect()}
              >
                Start Planning Today
              </Button>
            )}
          </motion.div>
        </div>
      </section>
    </div>
  );
};