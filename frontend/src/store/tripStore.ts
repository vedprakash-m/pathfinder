import { create } from 'zustand';
import { Trip, TripFilters, ApiError } from '@/types';

interface TripState {
  trips: Trip[];
  currentTrip: Trip | null;
  filters: TripFilters;
  isLoading: boolean;
  error: ApiError | null;
  
  // Actions
  setTrips: (trips: Trip[]) => void;
  addTrip: (trip: Trip) => void;
  updateTrip: (tripId: string, updates: Partial<Trip>) => void;
  removeTrip: (tripId: string) => void;
  setCurrentTrip: (trip: Trip | null) => void;
  setFilters: (filters: Partial<TripFilters>) => void;
  clearFilters: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: ApiError | null) => void;
  clearError: () => void;
}

const initialFilters: TripFilters = {
  status: undefined,
  date_range: undefined,
  destination: undefined,
  family_id: undefined,
};

export const useTripStore = create<TripState>()((set, get) => ({
  trips: [],
  currentTrip: null,
  filters: initialFilters,
  isLoading: false,
  error: null,

  setTrips: (trips: Trip[]) => {
    set({ trips, error: null });
  },

  addTrip: (trip: Trip) => {
    set((state) => ({
      trips: [trip, ...state.trips],
      error: null,
    }));
  },

  updateTrip: (tripId: string, updates: Partial<Trip>) => {
    set((state) => ({
      trips: state.trips.map((trip) =>
        trip.id === tripId ? { ...trip, ...updates } : trip
      ),
      currentTrip: state.currentTrip?.id === tripId 
        ? { ...state.currentTrip, ...updates }
        : state.currentTrip,
      error: null,
    }));
  },

  removeTrip: (tripId: string) => {
    set((state) => ({
      trips: state.trips.filter((trip) => trip.id !== tripId),
      currentTrip: state.currentTrip?.id === tripId ? null : state.currentTrip,
      error: null,
    }));
  },

  setCurrentTrip: (trip: Trip | null) => {
    set({ currentTrip: trip });
  },

  setFilters: (filters: Partial<TripFilters>) => {
    set((state) => ({
      filters: { ...state.filters, ...filters },
    }));
  },

  clearFilters: () => {
    set({ filters: initialFilters });
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },

  setError: (error: ApiError | null) => {
    set({ error });
  },

  clearError: () => {
    set({ error: null });
  },
}));