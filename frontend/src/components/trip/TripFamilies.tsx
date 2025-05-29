import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardHeader, Title2, Title3, Body1, Body2, Badge, Button } from '@fluentui/react-components';
import {
  UsersIcon,
  EnvelopeIcon,
  PlusIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

interface Family {
  id: string;
  name: string;
  status: 'confirmed' | 'pending' | 'declined';
  members: Array<{
    id: string;
    name: string;
    email: string;
    role: 'parent' | 'child';
  }>;
  preferences?: Record<string, any>;
}

interface TripFamiliesProps {
  families: Family[];
  tripId: string;
  onInviteFamily: () => void;
  onManageFamily: (familyId: string) => void;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'confirmed':
      return 'success';
    case 'pending':
      return 'warning';
    case 'declined':
      return 'danger';
    default:
      return 'subtle';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'confirmed':
      return <CheckCircleIcon className="w-4 h-4" />;
    case 'pending':
      return <ClockIcon className="w-4 h-4" />;
    case 'declined':
      return <ExclamationTriangleIcon className="w-4 h-4" />;
    default:
      return null;
  }
};

const FamilyCard: React.FC<{ family: Family; onManage: () => void }> = ({ family, onManage }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="mb-4 hover:shadow-md transition-shadow">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary-50 rounded-full flex items-center justify-center">
                <UsersIcon className="w-5 h-5 text-primary-600" />
              </div>
              <div>
                <Title3 className="text-neutral-900">{family.name}</Title3>
                <Body2 className="text-neutral-600">
                  {family.members.length} member{family.members.length !== 1 ? 's' : ''}
                </Body2>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge 
                color={getStatusColor(family.status)} 
                icon={getStatusIcon(family.status)}
                className="capitalize"
              >
                {family.status}
              </Badge>
            </div>
          </div>
        </CardHeader>
        
        <div className="p-4 pt-0">
          {/* Family Members */}
          <div className="space-y-2 mb-4">
            {family.members.map((member) => (
              <div key={member.id} className="flex items-center gap-3 p-2 bg-neutral-50 rounded-lg">
                <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-primary-600">
                    {member.name.split(' ').map(n => n[0]).join('')}
                  </span>
                </div>
                <div className="flex-1">
                  <Body2 className="font-medium">{member.name}</Body2>
                  <Body2 className="text-neutral-500 text-xs">{member.email}</Body2>
                </div>
                <Badge size="small" className="capitalize">
                  {member.role}
                </Badge>
              </div>
            ))}
          </div>

          {/* Preferences */}
          {family.preferences && Object.keys(family.preferences).length > 0 && (
            <div className="mb-4">
              <Body2 className="font-medium text-neutral-700 mb-2">Preferences</Body2>
              <div className="flex flex-wrap gap-1">
                {Object.entries(family.preferences).slice(0, 3).map(([key, value]) => (
                  <Badge key={key} size="small" className="text-xs">
                    {key}: {String(value)}
                  </Badge>
                ))}
                {Object.keys(family.preferences).length > 3 && (
                  <Badge size="small" className="text-xs">
                    +{Object.keys(family.preferences).length - 3} more
                  </Badge>
                )}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2">
            <Button appearance="outline" size="small" onClick={onManage}>
              Manage
            </Button>
            {family.status === 'pending' && (
              <Button 
                appearance="outline" 
                size="small"
                icon={<EnvelopeIcon className="w-4 h-4" />}
              >
                Resend Invite
              </Button>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

export const TripFamilies: React.FC<TripFamiliesProps> = ({
  families,
  tripId,
  onInviteFamily,
  onManageFamily,
}) => {
  const confirmedFamilies = families.filter(f => f.status === 'confirmed');
  const pendingFamilies = families.filter(f => f.status === 'pending');
  const declinedFamilies = families.filter(f => f.status === 'declined');

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="space-y-6"
    >
      {/* Overview Stats */}
      <div className="grid md:grid-cols-3 gap-4">
        <Card className="text-center p-4">
          <div className="w-12 h-12 bg-green-50 rounded-full mx-auto mb-3 flex items-center justify-center">
            <CheckCircleIcon className="w-6 h-6 text-green-600" />
          </div>
          <Title3 className="text-green-600">{confirmedFamilies.length}</Title3>
          <Body2 className="text-neutral-600">Confirmed</Body2>
        </Card>
        
        <Card className="text-center p-4">
          <div className="w-12 h-12 bg-amber-50 rounded-full mx-auto mb-3 flex items-center justify-center">
            <ClockIcon className="w-6 h-6 text-amber-600" />
          </div>
          <Title3 className="text-amber-600">{pendingFamilies.length}</Title3>
          <Body2 className="text-neutral-600">Pending</Body2>
        </Card>
        
        <Card className="text-center p-4">
          <div className="w-12 h-12 bg-red-50 rounded-full mx-auto mb-3 flex items-center justify-center">
            <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
          </div>
          <Title3 className="text-red-600">{declinedFamilies.length}</Title3>
          <Body2 className="text-neutral-600">Declined</Body2>
        </Card>
      </div>

      {/* Invite New Family */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <Title2>Family Management</Title2>
            <Button 
              appearance="primary"
              icon={<PlusIcon className="w-4 h-4" />}
              onClick={onInviteFamily}
            >
              Invite Family
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Confirmed Families */}
      {confirmedFamilies.length > 0 && (
        <div>
          <Title2 className="mb-4 text-green-600">Confirmed Families</Title2>
          {confirmedFamilies.map((family) => (
            <FamilyCard
              key={family.id}
              family={family}
              onManage={() => onManageFamily(family.id)}
            />
          ))}
        </div>
      )}

      {/* Pending Families */}
      {pendingFamilies.length > 0 && (
        <div>
          <Title2 className="mb-4 text-amber-600">Pending Invitations</Title2>
          {pendingFamilies.map((family) => (
            <FamilyCard
              key={family.id}
              family={family}
              onManage={() => onManageFamily(family.id)}
            />
          ))}
        </div>
      )}

      {/* Declined Families */}
      {declinedFamilies.length > 0 && (
        <div>
          <Title2 className="mb-4 text-red-600">Declined Invitations</Title2>
          {declinedFamilies.map((family) => (
            <FamilyCard
              key={family.id}
              family={family}
              onManage={() => onManageFamily(family.id)}
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {families.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-center py-12"
        >
          <div className="w-24 h-24 bg-primary-50 rounded-full mx-auto mb-6 flex items-center justify-center">
            <UsersIcon className="w-12 h-12 text-primary-600" />
          </div>
          <Title2 className="text-neutral-900 mb-4">No families yet</Title2>
          <Body1 className="text-neutral-600 mb-8 max-w-md mx-auto">
            Start building your trip group by inviting families to join this adventure.
          </Body1>
          <Button
            appearance="primary"
            size="large"
            icon={<PlusIcon className="w-5 h-5" />}
            onClick={onInviteFamily}
          >
            Invite First Family
          </Button>
        </motion.div>
      )}
    </motion.div>
  );
};
