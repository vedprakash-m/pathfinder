import { apiService } from './api';
import {
  Trip,
  CreateTripRequest,
  UpdateTripRequest,
  TripFilters,
  PaginatedResponse,
  ApiResponse,
} from '@/types';

export const tripService = {
  // Get all trips with optional filters
  getTrips: async (filters?: TripFilters): Promise<ApiResponse<PaginatedResponse<Trip>>> => {
    const params = new URLSearchParams();
    
    if (filters?.status?.length) {
      filters.status.forEach(status => params.append('status', status));
    }
    if (filters?.destination) {
      params.append('destination', filters.destination);
    }
    if (filters?.family_id) {
      params.append('family_id', filters.family_id);
    }
    if (filters?.date_range) {
      params.append('start_date_from', filters.date_range.start);
      params.append('start_date_to', filters.date_range.end);
    }

    const queryString = params.toString();
    const url = queryString ? `/trips/?${queryString}` : '/trips/';
    return apiService.get(url);
  },

  // Get user's trips (alias for getTrips for component compatibility)
  getUserTrips: async (filters?: TripFilters): Promise<ApiResponse<PaginatedResponse<Trip>>> => {
    return tripService.getTrips(filters);
  },

  // Get single trip by ID
  getTrip: async (tripId: string): Promise<ApiResponse<Trip>> => {
    return apiService.get(`/trips/${tripId}`);
  },

  // Get trip by ID (alias for getTrip for component compatibility)
  getTripById: async (tripId: string): Promise<ApiResponse<Trip>> => {
    return tripService.getTrip(tripId);
  },

  // Create new trip
  createTrip: async (tripData: CreateTripRequest): Promise<ApiResponse<Trip>> => {
    return apiService.post('/trips/', tripData, {
      invalidateUrlPatterns: ['trips']
    });
  },

  // Update existing trip
  updateTrip: async (tripId: string, tripData: UpdateTripRequest): Promise<ApiResponse<Trip>> => {
    return apiService.put(`/trips/${tripId}`, tripData, {
      invalidateUrlPatterns: ['trips']
    });
  },

  // Delete trip
  deleteTrip: async (tripId: string): Promise<ApiResponse<void>> => {
    return apiService.delete(`/trips/${tripId}`);
  },

  // Add participant to trip
  addParticipant: async (tripId: string, userId: string, role: 'organizer' | 'participant'): Promise<ApiResponse<Trip>> => {
    return apiService.post(`/trips/${tripId}/participants`, { user_id: userId, role });
  },

  // Remove participant from trip
  removeParticipant: async (tripId: string, userId: string): Promise<ApiResponse<Trip>> => {
    return apiService.delete(`/trips/${tripId}/participants/${userId}`);
  },

  // Update participant status
  updateParticipantStatus: async (
    tripId: string, 
    userId: string, 
    status: 'confirmed' | 'declined'
  ): Promise<ApiResponse<Trip>> => {
    return apiService.patch(`/trips/${tripId}/participants/${userId}`, { status });
  },

  // Generate AI itinerary
  generateItinerary: async (tripId: string, preferences?: Record<string, any>): Promise<ApiResponse<any>> => {
    return apiService.post(`/trips/${tripId}/generate-itinerary`, { preferences });
  },

  // Get trip statistics
  getTripStats: async (tripId: string): Promise<ApiResponse<any>> => {
    return apiService.get(`/trips/${tripId}/stats`);
  },

  // Export trip data
  exportTrip: async (tripId: string, format: 'pdf' | 'json'): Promise<ApiResponse<Blob>> => {
    return apiService.get(`/trips/${tripId}/export?format=${format}`, {
      responseType: 'blob'
    });
  },
};
