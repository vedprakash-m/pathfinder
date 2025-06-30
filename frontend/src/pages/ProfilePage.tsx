import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Card,
  CardHeader,
  Button,
  Title1,
  Title2,
  Title3,
  Body1,
  Body2,
  Input,
  Textarea,
  Switch,
  Field,
  Avatar,
  Badge,
} from '@fluentui/react-components';
import {
  UserIcon,
  BellIcon,
  ShieldCheckIcon,
  GlobeAltIcon,
  DevicePhoneMobileIcon,
  EnvelopeIcon,
} from '@heroicons/react/24/outline';
import { useAuthStore } from '@/store';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

const ProfileSection: React.FC = () => {
  const { user: authUser } = useAuth();
  const { user, updateProfile } = useAuthStore();
  
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: user?.name || authUser?.name || '',
    email: user?.email || authUser?.email || '',
    phone: user?.phone_number || '',
    bio: user?.bio || '',
    location: user?.location || '',
  });

  const queryClient = useQueryClient();

  const updateProfileMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      // This would call the actual API endpoint
      // For now, we'll just simulate the update
      await new Promise(resolve => setTimeout(resolve, 1000));
      return data;
    },
    onSuccess: (data) => {
      updateProfile(data);
      setIsEditing(false);
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfileMutation.mutate(formData);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <UserIcon className="w-6 h-6 text-primary-600" />
            <Title2>Profile Information</Title2>
          </div>
          <Button
            appearance={isEditing ? "outline" : "subtle"}
            onClick={() => {
              if (isEditing) {
                setFormData({
                  name: user?.name || '',
                  email: user?.email || '',
                  phone: user?.phone_number || '',
                  bio: user?.bio || '',
                  location: user?.location || '',
                });
              }
              setIsEditing(!isEditing);
            }}
          >
            {isEditing ? 'Cancel' : 'Edit'}
          </Button>
        </div>
      </CardHeader>
      <div style={{ padding: '16px' }}>
        <div className="flex flex-col sm:flex-row gap-6">
          <div className="flex flex-col items-center">
            <Avatar
              name={authUser?.name || user?.name || 'User'}
              size={96}
              className="mb-4"
            />
            <Badge color="success">Verified</Badge>
          </div>

          <div className="flex-1">
            {isEditing ? (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <Field label="Name">
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    />
                  </Field>
                  <Field label="Email">
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    />
                  </Field>
                </div>

                <div className="grid sm:grid-cols-2 gap-4">
                  <Field label="Phone">
                    <Input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    />
                  </Field>
                  <Field label="Location">
                    <Input
                      value={formData.location}
                      onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    />
                  </Field>
                </div>

                <Field label="Bio">
                  <Textarea
                    value={formData.bio}
                    onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                    rows={3}
                    placeholder="Tell us about yourself..."
                  />
                </Field>

                <div className="flex justify-end gap-3">
                  <Button
                    type="submit"
                    appearance="primary"
                    disabled={updateProfileMutation.isPending}
                  >
                    {updateProfileMutation.isPending ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                <div>
                  <Body2 className="font-medium text-neutral-700">Name</Body2>
                  <Body1 className="text-neutral-900">{user?.name || 'Not provided'}</Body1>
                </div>
                <div>
                  <Body2 className="font-medium text-neutral-700">Email</Body2>
                  <Body1 className="text-neutral-900">{user?.email || 'Not provided'}</Body1>
                </div>
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <Body2 className="font-medium text-neutral-700">Phone</Body2>
                    <Body1 className="text-neutral-900">{user?.phone_number || 'Not provided'}</Body1>
                  </div>
                  <div>
                    <Body2 className="font-medium text-neutral-700">Location</Body2>
                    <Body1 className="text-neutral-900">{user?.location || 'Not provided'}</Body1>
                  </div>
                </div>
                {user?.bio && (
                  <div>
                    <Body2 className="font-medium text-neutral-700">Bio</Body2>
                    <Body1 className="text-neutral-900">{user.bio}</Body1>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};

const NotificationSettings: React.FC = () => {
  const [settings, setSettings] = useState({
    emailNotifications: true,
    pushNotifications: true,
    tripUpdates: true,
    familyInvitations: true,
    itineraryChanges: true,
    marketingEmails: false,
  });

  const updateSetting = (key: keyof typeof settings, value: boolean) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <BellIcon className="w-6 h-6 text-primary-600" />
          <Title2>Notification Preferences</Title2>
        </div>
      </CardHeader>
      <div style={{ padding: '16px' }}>
        <div className="space-y-6">
          <div>
            <Title3 className="mb-4">Communication</Title3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <EnvelopeIcon className="w-5 h-5 text-neutral-600" />
                  <div>
                    <Body1 className="font-medium">Email Notifications</Body1>
                    <Body2 className="text-neutral-600">Receive important updates via email</Body2>
                  </div>
                </div>
                <Switch
                  checked={settings.emailNotifications}
                  onChange={(e) => updateSetting('emailNotifications', e.currentTarget.checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <DevicePhoneMobileIcon className="w-5 h-5 text-neutral-600" />
                  <div>
                    <Body1 className="font-medium">Push Notifications</Body1>
                    <Body2 className="text-neutral-600">Get real-time updates on your device</Body2>
                  </div>
                </div>
                <Switch
                  checked={settings.pushNotifications}
                  onChange={(e) => updateSetting('pushNotifications', e.currentTarget.checked)}
                />
              </div>
            </div>
          </div>

          <div>
            <Title3 className="mb-4">Trip Updates</Title3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Body1 className="font-medium">Trip Updates</Body1>
                  <Body2 className="text-neutral-600">Changes to trip status and details</Body2>
                </div>
                <Switch
                  checked={settings.tripUpdates}
                  onChange={(e) => updateSetting('tripUpdates', e.currentTarget.checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Body1 className="font-medium">Family Invitations</Body1>
                  <Body2 className="text-neutral-600">New family invitations and join requests</Body2>
                </div>
                <Switch
                  checked={settings.familyInvitations}
                  onChange={(e) => updateSetting('familyInvitations', e.currentTarget.checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Body1 className="font-medium">Itinerary Changes</Body1>
                  <Body2 className="text-neutral-600">Updates to trip itineraries and schedules</Body2>
                </div>
                <Switch
                  checked={settings.itineraryChanges}
                  onChange={(e) => updateSetting('itineraryChanges', e.currentTarget.checked)}
                />
              </div>
            </div>
          </div>

          <div>
            <Title3 className="mb-4">Marketing</Title3>
            <div className="flex items-center justify-between">
              <div>
                <Body1 className="font-medium">Marketing Emails</Body1>
                <Body2 className="text-neutral-600">Tips, features, and promotional content</Body2>
              </div>
              <Switch
                checked={settings.marketingEmails}
                onChange={(e) => updateSetting('marketingEmails', e.currentTarget.checked)}
              />
            </div>
          </div>

          <Button appearance="primary" className="w-full sm:w-auto">
            Save Preferences
          </Button>
        </div>
      </div>
    </Card>
  );
};

const PrivacySettings: React.FC = () => {
  const [settings, setSettings] = useState({
    profileVisibility: 'family',
    showTripHistory: true,
    allowFamilyInvites: true,
    shareLocation: false,
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <ShieldCheckIcon className="w-6 h-6 text-primary-600" />
          <Title2>Privacy Settings</Title2>
        </div>
      </CardHeader>
      <div style={{ padding: '16px' }}>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <Body1 className="font-medium">Show Trip History</Body1>
              <Body2 className="text-neutral-600">Allow family members to see your past trips</Body2>
            </div>
            <Switch
              checked={settings.showTripHistory}
              onChange={(e) => setSettings({ ...settings, showTripHistory: e.currentTarget.checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Body1 className="font-medium">Allow Family Invites</Body1>
              <Body2 className="text-neutral-600">Let others invite you to their family groups</Body2>
            </div>
            <Switch
              checked={settings.allowFamilyInvites}
              onChange={(e) => setSettings({ ...settings, allowFamilyInvites: e.currentTarget.checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Body1 className="font-medium">Share Location</Body1>
              <Body2 className="text-neutral-600">Share your location during active trips</Body2>
            </div>
            <Switch
              checked={settings.shareLocation}
              onChange={(e) => setSettings({ ...settings, shareLocation: e.currentTarget.checked })}
            />
          </div>

          <Button appearance="primary" className="w-full sm:w-auto">
            Save Settings
          </Button>
        </div>
      </div>
    </Card>
  );
};

const AccountSettings: React.FC = () => {
  const { logout } = useAuth();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <GlobeAltIcon className="w-6 h-6 text-primary-600" />
          <Title2>Account Settings</Title2>
        </div>
      </CardHeader>
      <div style={{ padding: '16px' }}>
        <div className="space-y-6">
          <div>
            <Body1 className="font-medium text-neutral-900 mb-2">Account Status</Body1>
            <div className="flex items-center gap-2">
              <Badge color="success">Active</Badge>
              <Body2 className="text-neutral-600">Premium Plan</Body2>
            </div>
          </div>

          <div className="border-t border-neutral-200 pt-6">
            <Body1 className="font-medium text-neutral-900 mb-4">Danger Zone</Body1>
            <div className="space-y-3">
              <Button
                appearance="outline"
                onClick={() => logout()}
              >
                Sign Out
              </Button>
              <div>
                <Button appearance="outline" className="text-error-600 border-error-200 hover:bg-error-50">
                  Delete Account
                </Button>
                <Body2 className="text-neutral-600 mt-1">
                  Permanently delete your account and all associated data
                </Body2>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

export const ProfilePage: React.FC = () => {
  const { isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Title1 className="text-neutral-900 mb-2">Profile Settings</Title1>
        <Body1 className="text-neutral-600">
          Manage your account information, preferences, and privacy settings
        </Body1>
      </motion.div>

      {/* Profile Information */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <ProfileSection />
      </motion.div>

      {/* Notification Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <NotificationSettings />
      </motion.div>

      {/* Privacy Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
      >
        <PrivacySettings />
      </motion.div>

      {/* Account Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        <AccountSettings />
      </motion.div>
    </div>
  );
};
