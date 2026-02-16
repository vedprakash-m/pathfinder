import { apiService } from './api';
import {
  Family,
  CreateFamilyRequest,
  InviteFamilyMemberRequest,
  PaginatedResponse,
  ApiResponse,
} from '@/types';

export const familyService = {
  // Get all families for current user
  getFamilies: async (): Promise<ApiResponse<PaginatedResponse<Family>>> => {
    return apiService.get('/families/');
  },

  // Get single family by ID
  getFamily: async (familyId: string): Promise<ApiResponse<Family>> => {
    return apiService.get(`/families/${familyId}`);
  },

  // Create new family
  createFamily: async (familyData: CreateFamilyRequest): Promise<ApiResponse<Family>> => {
    return apiService.post('/families/', familyData, {
      invalidateUrlPatterns: ['families']
    });
  },

  // Update family
  updateFamily: async (familyId: string, familyData: Partial<CreateFamilyRequest>): Promise<ApiResponse<Family>> => {
    return apiService.patch(`/families/${familyId}`, familyData, {
      invalidateUrlPatterns: ['families']
    });
  },

  // Delete family
  deleteFamily: async (familyId: string): Promise<ApiResponse<void>> => {
    return apiService.delete(`/families/${familyId}`, {
      invalidateUrlPatterns: ['families']
    });
  },

  // Invite family member
  inviteMember: async (familyId: string, inviteData: InviteFamilyMemberRequest): Promise<ApiResponse<{ invitation_id: string; expires_at: string }>> => {
    return apiService.post(`/families/${familyId}/invite`, inviteData, {
      invalidateUrlPatterns: ['families']
    });
  },

  // Remove family member
  removeMember: async (familyId: string, userId: string): Promise<ApiResponse<Family>> => {
    return apiService.delete(`/families/${familyId}/members/${userId}`);
  },

  // Update member role
  updateMemberRole: async (
    familyId: string,
    userId: string,
    role: 'admin' | 'member',
    permissions: string[]
  ): Promise<ApiResponse<Family>> => {
    return apiService.patch(`/families/${familyId}/members/${userId}`, { role, permissions });
  },

  // Accept family invitation
  acceptInvitation: async (invitationToken: string): Promise<ApiResponse<Family>> => {
    return apiService.post('/families/accept-invitation', { token: invitationToken });
  },

  // Decline family invitation
  declineInvitation: async (invitationToken: string): Promise<ApiResponse<void>> => {
    return apiService.post('/families/decline-invitation', { token: invitationToken });
  },

  // Leave family
  leaveFamily: async (familyId: string): Promise<ApiResponse<void>> => {
    return apiService.post(`/families/${familyId}/leave`);
  },
};
