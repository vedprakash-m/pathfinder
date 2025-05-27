import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
  Badge,
  Input,
  Dropdown,
  Option,
  Avatar,
  Field,
} from '@fluentui/react-components';
import {
  PlusIcon,
  UsersIcon,
  EnvelopeIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import { familyService } from '@/services/familyService';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useFormValidation } from '@/hooks/useFormValidation';
import { createFamilySchema, inviteFamilyMemberSchema } from '@/utils/validation';
import type { Family, FamilyMembershipStatus, CreateFamilyRequest, InviteFamilyMemberRequest } from '@/types';

const StatusBadge: React.FC<{ status: FamilyMembershipStatus }> = ({ status }) => {
  const getStatusColor = (status: FamilyMembershipStatus) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'pending':
        return 'warning';
      case 'inactive':
        return 'subtle';
      default:
        return 'subtle';
    }
  };

  return (
    <Badge color={getStatusColor(status)} className="capitalize">
      {status}
    </Badge>
  );
};

const FamilyCard: React.FC<{ family: Family & { membership_status: FamilyMembershipStatus, member_count: number } }> = ({ family }) => {
  const queryClient = useQueryClient();

  const leaveFamilyMutation = useMutation({
    mutationFn: () => familyService.leaveFamily(family.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['families'] });
    },
  });

  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="h-full border-2 border-transparent hover:border-primary-100 transition-colors">
        <CardHeader>
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-3">
              <Avatar
                name={family.name}
                size={48}
                className="bg-primary-100 text-primary-700"
              />
              <div>
                <Title3 className="text-neutral-900 mb-1">{family.name}</Title3>
                <div className="flex items-center gap-2">
                  <StatusBadge status={family.membership_status} />
                  <Body2 className="text-neutral-600">
                    {family.member_count} {family.member_count === 1 ? 'member' : 'members'}
                  </Body2>
                </div>
              </div>
            </div>
          </div>
        </CardHeader>
        <div className="p-4">
          <div className="space-y-4">
            {family.description && (
              <Body2 className="text-neutral-600 line-clamp-2">
                {family.description}
              </Body2>
            )}
            
            <div className="flex justify-between items-center">
              <Body2 className="text-neutral-500">
                Created {new Date(family.created_at).toLocaleDateString()}
              </Body2>
              
              {family.membership_status === 'active' && (
                <Button
                  appearance="subtle"
                  size="small"
                  onClick={() => leaveFamilyMutation.mutate()}
                  disabled={leaveFamilyMutation.isPending}
                >
                  Leave
                </Button>
              )}
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

const CreateFamilyForm: React.FC<{
  onSuccess: () => void;
  onCancel: () => void;
}> = ({ onSuccess, onCancel }) => {
  const initialFormData = {
    name: '',
    description: '',
  };

  const {
    formData,
    errors,
    updateFormData,
    validateAll,
    getFieldState,
    handleBlur
  } = useFormValidation(createFamilySchema, initialFormData);

  const queryClient = useQueryClient();

  const createFamilyMutation = useMutation({
    mutationFn: () => familyService.createFamily(formData as CreateFamilyRequest),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['families'] });
      onSuccess();
    },
    onError: () => {
      // Add a general error
      const updatedErrors = { ...errors, general: 'Failed to create family. Please try again.' };
      Object.assign(errors, updatedErrors);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateAll()) {
      return;
    }

    createFamilyMutation.mutate();
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Card>
        <CardHeader>
          <Title3>Create New Family</Title3>
        </CardHeader>
        <div className="p-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Field
              label="Family Name"
              required
              validationState={getFieldState('name').validationState === 'error' ? 'error' : 'none'}
              validationMessage={getFieldState('name').error}
            >
              <Input
                placeholder="Family name (e.g., The Smiths)"
                value={formData.name}
                onChange={(e) => updateFormData({ name: e.target.value })}
                onBlur={() => handleBlur('name')}
              />
            </Field>

            <Field label="Description">
              <Input
                placeholder="Description (optional)"
                value={formData.description || ''}
                onChange={(e) => updateFormData({ description: e.target.value })}
              />
            </Field>

            {errors.general && (
              <Body2 className="text-error-600">{errors.general}</Body2>
            )}

            <div className="flex justify-end gap-3">
              <Button
                appearance="outline"
                onClick={onCancel}
                disabled={createFamilyMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                appearance="primary"
                disabled={createFamilyMutation.isPending}
              >
                {createFamilyMutation.isPending ? 'Creating...' : 'Create Family'}
              </Button>
            </div>
          </form>
        </div>
      </Card>
    </motion.div>
  );
};

const InviteMemberForm: React.FC<{
  onSuccess: () => void;
  onCancel: () => void;
}> = ({ onSuccess, onCancel }) => {
  const initialFormData = {
    family_id: '',
    email: '',
    role: 'member' as const
  };

  const {
    formData,
    errors,
    updateFormData,
    validateAll,
    getFieldState,
    handleBlur
  } = useFormValidation(inviteFamilyMemberSchema, initialFormData);

  const queryClient = useQueryClient();

  const { data: families } = useQuery({
    queryKey: ['families'],
    queryFn: familyService.getFamilies,
  });

  const inviteMemberMutation = useMutation({
    mutationFn: () => {
      if (!formData.family_id) {
        throw new Error('Family ID is required');
      }
      return familyService.inviteMember(formData.family_id, {
        email: formData.email,
        role: 'member',
        permissions: []
      } as InviteFamilyMemberRequest);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['families'] });
      onSuccess();
    },
    onError: () => {
      // Add a general error
      const updatedErrors = { ...errors, general: 'Failed to send invitation. Please try again.' };
      Object.assign(errors, updatedErrors);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateAll()) {
      return;
    }

    inviteMemberMutation.mutate();
  };

  const familiesData = families?.data?.items || [];
  const activeFamilies = familiesData.filter((f: Family) => 
    f.members.some(member => member.role === 'admin')
  );

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Card>
        <CardHeader>
          <Title3>Invite Family Member</Title3>
        </CardHeader>
        <div className="p-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Field
              label="Select Family"
              required
              validationState={getFieldState('family_id').validationState === 'error' ? 'error' : 'none'}
              validationMessage={getFieldState('family_id').error}
            >
              <Dropdown
                placeholder="Select family"
                selectedOptions={formData.family_id ? [formData.family_id] : []}
                onOptionSelect={(_, data) => {
                  updateFormData({ family_id: data.optionValue as string });
                }}
                onBlur={() => handleBlur('family_id')}
              >
                {activeFamilies.map((family: Family) => (
                  <Option key={family.id} value={family.id} text={family.name}>
                    {family.name}
                  </Option>
                ))}
              </Dropdown>
            </Field>

            <Field
              label="Email Address"
              required
              validationState={getFieldState('email').validationState === 'error' ? 'error' : 'none'}
              validationMessage={getFieldState('email').error}
            >
              <Input
                type="email"
                placeholder="Email address"
                value={formData.email}
                onChange={(e) => updateFormData({ email: e.target.value })}
                onBlur={() => handleBlur('email')}
                contentBefore={<EnvelopeIcon className="w-4 h-4" />}
              />
            </Field>

            {errors.general && (
              <Body2 className="text-error-600">{errors.general}</Body2>
            )}

            <div className="flex justify-end gap-3">
              <Button
                appearance="outline"
                onClick={onCancel}
                disabled={inviteMemberMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                appearance="primary"
                disabled={inviteMemberMutation.isPending}
              >
                {inviteMemberMutation.isPending ? 'Sending...' : 'Send Invitation'}
              </Button>
            </div>
          </form>
        </div>
      </Card>
    </motion.div>
  );
};

export const FamiliesPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showInviteForm, setShowInviteForm] = useState(false);

  const { data: familiesResponse, isLoading, error } = useQuery({
    queryKey: ['families'],
    queryFn: familyService.getFamilies,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Extract the families data and add UI-specific properties
  const families = familiesResponse?.data?.items.map(family => {
    // Determine membership status based on whether the user is an admin
    const membershipStatus: FamilyMembershipStatus = 
      family.members.some(m => m.role === 'admin') ? 'active' : 'pending';
    
    return {
      ...family,
      membership_status: membershipStatus,
      member_count: family.members.length
    };
  }) || [];

  const filteredFamilies = families.filter(family =>
    family.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const activeFamilies = filteredFamilies.filter(f => f.membership_status === 'active');
  const pendingFamilies = filteredFamilies.filter(f => f.membership_status === 'pending');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <Title2 className="text-error-600 mb-4">Error Loading Families</Title2>
        <Body1 className="text-neutral-600 mb-6">
          We couldn't load your families. Please try again.
        </Body1>
        <Button appearance="primary" onClick={() => window.location.reload()}>
          Retry
        </Button>
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
        className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"
      >
        <div>
          <Title1 className="text-neutral-900 mb-2">Family Groups</Title1>
          <Body1 className="text-neutral-600">
            {families.length === 0 
              ? "Create or join family groups to plan trips together" 
              : `${activeFamilies.length} active ${activeFamilies.length === 1 ? 'family' : 'families'}`
            }
          </Body1>
        </div>
        <div className="flex gap-3">
          <Button
            appearance="outline"
            icon={<EnvelopeIcon className="w-5 h-5" />}
            onClick={() => setShowInviteForm(true)}
            disabled={activeFamilies.length === 0}
          >
            Invite Member
          </Button>
          <Button
            appearance="primary"
            icon={<PlusIcon className="w-5 h-5" />}
            onClick={() => setShowCreateForm(true)}
          >
            Create Family
          </Button>
        </div>
      </motion.div>

      {/* Create Family Form */}
      {showCreateForm && (
        <CreateFamilyForm
          onSuccess={() => setShowCreateForm(false)}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      {/* Invite Member Form */}
      {showInviteForm && (
        <InviteMemberForm
          onSuccess={() => setShowInviteForm(false)}
          onCancel={() => setShowInviteForm(false)}
        />
      )}

      {/* Search */}
      {families.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <Card>
            <div className="p-4">
              <Input
                type="text"
                placeholder="Search families..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                contentBefore={<MagnifyingGlassIcon className="w-4 h-4" />}
              />
            </div>
          </Card>
        </motion.div>
      )}

      {/* Pending Invitations */}
      {pendingFamilies.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <Title2 className="mb-6">Pending Invitations ({pendingFamilies.length})</Title2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {pendingFamilies.map((family, index) => (
              <motion.div
                key={family.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.3 + index * 0.1 }}
              >
                <FamilyCard family={family} />
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Active Families */}
      {activeFamilies.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <Title2 className="mb-6">Your Families ({activeFamilies.length})</Title2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {activeFamilies.map((family, index) => (
              <motion.div
                key={family.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.5 + index * 0.1 }}
              >
                <FamilyCard family={family} />
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Empty State */}
      {filteredFamilies.length === 0 && families.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-center py-12"
        >
          <Title2 className="text-neutral-900 mb-4">No families found</Title2>
          <Body1 className="text-neutral-600 mb-6">
            Try adjusting your search to find what you're looking for.
          </Body1>
          <Button 
            appearance="outline" 
            onClick={() => setSearchTerm('')}
          >
            Clear Search
          </Button>
        </motion.div>
      )}

      {/* No Families Empty State */}
      {families.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-center py-12"
        >
          <div className="w-24 h-24 bg-primary-50 rounded-full mx-auto mb-6 flex items-center justify-center">
            <UsersIcon className="w-12 h-12 text-primary-600" />
          </div>
          <Title2 className="text-neutral-900 mb-4">No families yet</Title2>
          <Body1 className="text-neutral-600 mb-8 max-w-md mx-auto">
            Create your first family group to start planning trips together with your loved ones.
          </Body1>
          <Button
            appearance="primary"
            size="large"
            icon={<PlusIcon className="w-5 h-5" />}
            onClick={() => setShowCreateForm(true)}
          >
            Create Your First Family
          </Button>
        </motion.div>
      )}
    </div>
  );
};
