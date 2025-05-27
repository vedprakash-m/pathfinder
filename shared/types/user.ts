export interface User {
  id: string;
  email: string;
  full_name: string;
  profile_picture_url?: string;
  phone_number?: string;
  date_of_birth?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  preferences?: Record<string, any>;
  is_active: boolean;
  auth0_user_id?: string;
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

export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface PasswordReset {
  token: string;
  new_password: string;
}

export interface UserPermissions {
  trips: {
    create: boolean;
    update: boolean;
    delete: boolean;
  };
  families: {
    create: boolean;
    update: boolean;
    delete: boolean;
  };
  admin: boolean;
}