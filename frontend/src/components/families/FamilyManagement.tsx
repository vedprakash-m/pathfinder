import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  Button,
  Input,
  Text,
  Title2,
  Title3,
  Body1,
  Dialog,
  DialogTrigger,
  DialogSurface,
  DialogTitle,
  DialogContent,
  DialogBody,
  DialogActions,
  Field,
  Textarea,
  Badge,
  Menu,
  MenuTrigger,
  MenuPopover,
  MenuList,
  MenuItem,
  MenuButton,
} from '@fluentui/react-components';
import {
  PlusIcon,
  UserPlusIcon,
  EllipsisVerticalIcon,
  TrashIcon,
  PencilIcon,
} from '@heroicons/react/24/outline';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { familyService } from '@/services/familyService';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { Family, CreateFamilyRequest, InviteFamilyMemberRequest } from '@/types';

interface FamilyManagementProps {
  className?: string;
}

interface CreateFamilyDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateFamilyRequest) => void;
  isLoading?: boolean;
}

interface ExtendedInviteFamilyMemberRequest extends InviteFamilyMemberRequest {
  message?: string;
}

interface InviteMemberDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: InviteFamilyMemberRequest) => void;
  isLoading?: boolean;
}

const CreateFamilyDialog: React.FC<CreateFamilyDialogProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
}) => {
  const [formData, setFormData] = useState<CreateFamilyRequest>({
    name: '',
    description: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogSurface>
        <form onSubmit={handleSubmit}>
          <DialogBody>
            <DialogTitle>Create New Family</DialogTitle>
            <DialogContent>
              <Field label="Family Name" required>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Enter family name"
                  required
                />
              </Field>
              <Field label="Description">
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Enter family description (optional)"
                  rows={3}
                />
              </Field>
            </DialogContent>
          </DialogBody>
          <DialogActions>
            <DialogTrigger disableButtonEnhancement>
              <Button appearance="secondary" onClick={onClose}>
                Cancel
              </Button>
            </DialogTrigger>
            <Button
              type="submit"
              appearance="primary"
              disabled={!formData.name.trim() || isLoading}
            >
              {isLoading ? 'Creating...' : 'Create Family'}
            </Button>
          </DialogActions>
        </form>
      </DialogSurface>
    </Dialog>
  );
};

const InviteMemberDialog: React.FC<InviteMemberDialogProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
}) => {
  const [formData, setFormData] = useState<ExtendedInviteFamilyMemberRequest>({
    email: '',
    role: 'member',
    permissions: [],
    message: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Extract only the required fields for the API
    const { message: _message, ...apiData } = formData;
    onSubmit(apiData);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogSurface>
        <form onSubmit={handleSubmit}>
          <DialogBody>
            <DialogTitle>Invite Family Member</DialogTitle>
            <DialogContent>
              <Field label="Email Address" required>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="Enter email address"
                  required
                />
              </Field>
              <Field label="Personal Message">
                <Textarea
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  placeholder="Add a personal message (optional)"
                  rows={3}
                />
              </Field>
            </DialogContent>
          </DialogBody>
          <DialogActions>
            <DialogTrigger disableButtonEnhancement>
              <Button appearance="secondary" onClick={onClose}>
                Cancel
              </Button>
            </DialogTrigger>
            <Button
              type="submit"
              appearance="primary"
              disabled={!formData.email.trim() || isLoading}
            >
              {isLoading ? 'Sending...' : 'Send Invitation'}
            </Button>
          </DialogActions>
        </form>
      </DialogSurface>
    </Dialog>
  );
};

const FamilyCard: React.FC<{ family: Family; onEdit: () => void; onDelete: () => void; onInvite: () => void }> = ({
  family,
  onEdit,
  onDelete,
  onInvite,
}) => {
  return (
    <Card className="w-full">
      <CardHeader
        header={
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <Title3>{family.name}</Title3>
              <Body1 className="text-gray-600 mt-1">
                {family.description || 'No description'}
              </Body1>
              <div className="flex items-center gap-2 mt-2">
                <Badge color="informative">
                  {family.members?.length || 0} members
                </Badge>
              </div>
            </div>
            <Menu>
              <MenuTrigger disableButtonEnhancement>
                <MenuButton
                  appearance="subtle"
                  icon={<EllipsisVerticalIcon className="w-4 h-4" />}
                />
              </MenuTrigger>
              <MenuPopover>
                <MenuList>
                  <MenuItem icon={<UserPlusIcon className="w-4 h-4" />} onClick={onInvite}>
                    Invite Member
                  </MenuItem>
                  <MenuItem icon={<PencilIcon className="w-4 h-4" />} onClick={onEdit}>
                    Edit Family
                  </MenuItem>
                  <MenuItem icon={<TrashIcon className="w-4 h-4" />} onClick={onDelete}>
                    Delete Family
                  </MenuItem>
                </MenuList>
              </MenuPopover>
            </Menu>
          </div>
        }
      />
    </Card>
  );
};

export const FamilyManagement: React.FC<FamilyManagementProps> = ({ className = '' }) => {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [selectedFamilyId, setSelectedFamilyId] = useState<string>('');

  const queryClient = useQueryClient();

  // Fetch families
  const {
    data: familiesResponse,
    isLoading,
    error
  } = useQuery({
    queryKey: ['families'],
    queryFn: () => familyService.getFamilies(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const families = familiesResponse?.data?.items || [];

  // Create family mutation
  const createFamilyMutation = useMutation({
    mutationFn: (data: CreateFamilyRequest) => familyService.createFamily(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['families'] });
      setCreateDialogOpen(false);
    },
  });

  // Invite member mutation
  const inviteMemberMutation = useMutation({
    mutationFn: ({ familyId, data }: { familyId: string; data: InviteFamilyMemberRequest }) =>
      familyService.inviteMember(familyId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['families'] });
      setInviteDialogOpen(false);
      setSelectedFamilyId('');
    },
  });

  // Delete family mutation
  const deleteFamilyMutation = useMutation({
    mutationFn: (familyId: string) => familyService.deleteFamily(familyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['families'] });
    },
  });

  const handleCreateFamily = (data: CreateFamilyRequest) => {
    createFamilyMutation.mutate(data);
  };

  const handleInviteMember = (data: InviteFamilyMemberRequest) => {
    if (selectedFamilyId) {
      inviteMemberMutation.mutate({ familyId: selectedFamilyId, data });
    }
  };

  const handleDeleteFamily = (familyId: string) => {
    if (confirm('Are you sure you want to delete this family?')) {
      deleteFamilyMutation.mutate(familyId);
    }
  };

  const openInviteDialog = (familyId: string) => {
    setSelectedFamilyId(familyId);
    setInviteDialogOpen(true);
  };

  if (isLoading) {
    return <LoadingSpinner label="Loading families..." />;
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <Text className="text-red-600">
          Error loading families. Please try again.
        </Text>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <Title2>Family Management</Title2>
        <Button
          appearance="primary"
          icon={<PlusIcon className="w-4 h-4" />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Create Family
        </Button>
      </div>

      {/* Families List */}
      {families.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Title3 className="text-gray-600 mb-2">No families yet</Title3>
          <Body1 className="text-gray-500 mb-4">
            Create your first family to start planning trips together.
          </Body1>
          <Button
            appearance="primary"
            onClick={() => setCreateDialogOpen(true)}
            icon={<PlusIcon className="w-4 h-4" />}
          >
            Create Your First Family
          </Button>
        </div>
      ) : (
        <div className="grid gap-4">
          {families.map((family) => (
            <FamilyCard
              key={family.id}
              family={family}
              onEdit={() => {/* TODO: Implement edit */}}
              onDelete={() => handleDeleteFamily(family.id)}
              onInvite={() => openInviteDialog(family.id)}
            />
          ))}
        </div>
      )}

      {/* Dialogs */}
      <CreateFamilyDialog
        isOpen={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSubmit={handleCreateFamily}
        isLoading={createFamilyMutation.isPending}
      />

      <InviteMemberDialog
        isOpen={inviteDialogOpen}
        onClose={() => {
          setInviteDialogOpen(false);
          setSelectedFamilyId('');
        }}
        onSubmit={handleInviteMember}
        isLoading={inviteMemberMutation.isPending}
      />
    </div>
  );
};

export default FamilyManagement;
