import React from 'react';
import { Title1, Body1 } from '@fluentui/react-components';

const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <Title1 className="text-neutral-900 mb-2">Settings</Title1>
        <Body1 className="text-neutral-600">
          Manage your application settings and preferences.
        </Body1>
      </div>
    </div>
  );
};

export default SettingsPage;