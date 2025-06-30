// Core API response types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// User roles aligned with UX specification
export enum UserRole {
  SUPER_ADMIN = "super_admin",
  FAMILY_ADMIN = "family_admin",
  TRIP_ORGANIZER = "trip_organizer",
  FAMILY_MEMBER = "family_member"
}

// User and Authentication types
export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole; // 🔑 ADD ROLE FIELD
  full_name?: string;
  picture?: string;
  phone_number?: string;
  bio?: string;
  location?: string;
  preferences?: UserPreferences;
  created_at: string;
  updated_at: string;
}

export interface UserProfile extends User {
  families: {
    id: string;
    name: string;
    role: 'admin' | 'member';
    created_at: string;
  }[];
  trips_count: number;
}

export interface AuthCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  phone_number?: string;
  date_of_birth?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  profile_picture_url?: string;
  preferences?: Record<string, any>;
}

// User creation interface for backend integration (for Entra ID users)
export interface UserCreate {
  email: string;
  name: string;
  entra_id: string;
  picture?: string;
  phone?: string;
  preferences?: Record<string, any>;
}

export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface UserPreferences {
  budget_range?: string;
  travel_style?: string;
  accommodation_type?: string;
  transportation_mode?: string;
  activity_preferences?: string[];
  dietary_restrictions?: string[];
  accessibility_needs?: string[];
}

// Family types
export interface Family {
  id: string;
  name: string;
  description?: string;
  admin_id: string;
  members: FamilyMember[];
  created_at: string;
  updated_at: string;
}

export interface FamilyMember {
  user_id: string;
  role: 'admin' | 'member';
  permissions: string[];
  joined_at: string;
  user?: User;
}

// Add FamilyMembershipStatus type after Family interface
export type FamilyMembershipStatus = 'active' | 'pending' | 'inactive';

// Add extendedFamily interface for UI usage
export interface ExtendedFamily extends Family {
  membership_status: FamilyMembershipStatus;
  member_count: number;
}

// Trip types
export interface Trip {
  id: string;
  title: string;
  name: string; // alias for title for component compatibility
  description?: string;
  destination: string;
  start_date: string;
  end_date: string;
  status: TripStatus;
  budget?: number;
  budget_total?: number; // for component compatibility
  family_id: string;
  family_count: number;
  confirmed_families: number;
  created_by: string;
  itinerary?: Itinerary;
  participants: TripParticipant[];
  reservations: Reservation[];
  created_at: string;
  updated_at: string;
}

export type TripStatus = 'planning' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled';

export interface TripParticipant {
  user_id: string;
  role: 'organizer' | 'participant';
  status: 'pending' | 'confirmed' | 'declined';
  user?: User;
}

// Itinerary types
export interface Itinerary {
  id: string;
  trip_id: string;
  title: string;
  days: ItineraryDay[];
  ai_generated: boolean;
  created_at: string;
  updated_at: string;
}

export interface ItineraryDay {
  date: string;
  activities: Activity[];
}

export interface Activity {
  id: string;
  title: string;
  description?: string;
  location: Location;
  start_time?: string;
  end_time?: string;
  duration?: number; // minutes
  category: ActivityCategory;
  cost?: number;
  booking_required: boolean;
  notes?: string;
}

export type ActivityCategory = 
  | 'accommodation' 
  | 'transportation' 
  | 'dining' 
  | 'sightseeing' 
  | 'entertainment' 
  | 'shopping' 
  | 'outdoor' 
  | 'cultural' 
  | 'relaxation'
  | 'other';

export interface Location {
  name: string;
  address?: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  place_id?: string;
}

// Reservation types
export interface Reservation {
  id: string;
  trip_id: string;
  activity_id?: string;
  type: ReservationType;
  provider: string;
  confirmation_number?: string;
  status: ReservationStatus;
  cost: number;
  currency: string;
  details: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export type ReservationType = 'flight' | 'hotel' | 'restaurant' | 'activity' | 'rental' | 'other';
export type ReservationStatus = 'pending' | 'confirmed' | 'cancelled' | 'completed';

// AI and Maps integration types
export interface AIRecommendation {
  activity: Activity;
  confidence: number;
  reasoning: string;
  alternatives?: Activity[];
}

export interface PlaceDetails {
  place_id: string;
  name: string;
  formatted_address: string;
  location: {
    lat: number;
    lng: number;
  };
  rating?: number;
  price_level?: number;
  photos?: string[];
  opening_hours?: string[];
  website?: string;
  phone?: string;
  types: string[];
}

// WebSocket message types
export interface WebSocketMessage<T = any> {
  type: 'trip_update' | 'itinerary_update' | 'reservation_update' | 'family_update' | 'notification';
  message_type: string;
  data: T;
  payload: T;
  timestamp: string;
  user_id?: string;
  room_id?: string;
}

// Form types for creating/updating
export interface CreateTripRequest {
  title: string;
  description?: string;
  destination: string;
  start_date: string;
  end_date: string;
  budget?: number;
  family_id: string;
}

export interface UpdateTripRequest extends Partial<CreateTripRequest> {
  status?: TripStatus;
}

export interface CreateFamilyRequest {
  name: string;
  description?: string;
}

export interface InviteFamilyMemberRequest {
  email: string;
  role: 'admin' | 'member';
  permissions: string[];
}

// UI State types
export interface TripFilters {
  status?: TripStatus[];
  date_range?: {
    start: string;
    end: string;
  };
  destination?: string;
  family_id?: string;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  sms: boolean;
  trip_updates: boolean;
  reservation_updates: boolean;
  family_updates: boolean;
}

// Error types
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}
