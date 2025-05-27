import { z } from 'zod';

// Common validation schemas
export const emailSchema = z
  .string()
  .email('Invalid email address')
  .min(1, 'Email is required');

export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number')
  .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character');

export const nameSchema = z
  .string()
  .min(1, 'Name is required')
  .max(100, 'Name must be less than 100 characters');

export const phoneSchema = z
  .string()
  .regex(/^\+?[0-9]{10,15}$/, 'Invalid phone number')
  .optional()
  .or(z.literal(''));

export const dateSchema = z.string().refine(
  (date) => {
    if (!date) return false;
    const parsedDate = new Date(date);
    return !isNaN(parsedDate.getTime());
  },
  { message: 'Invalid date format' }
);

export const futureDateSchema = dateSchema.refine(
  (date) => {
    if (!date) return false;
    const parsedDate = new Date(date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return parsedDate >= today;
  },
  { message: 'Date must be in the future' }
);

// Trip schemas
export const createTripSchema = z
  .object({
    name: nameSchema,
    description: z.string().optional(),
    destination: z.string().min(1, 'Destination is required'),
    start_date: futureDateSchema.refine((date) => !!date, {
      message: 'Start date is required',
    }),
    end_date: dateSchema.refine((date) => !!date, {
      message: 'End date is required',
    }),
    budget_total: z
      .number()
      .nonnegative('Budget must be a positive number')
      .optional(),
    is_public: z.boolean().optional(),
    preferences: z.record(z.any()).optional(),
  })
  .refine(
    (data) => {
      if (!data.start_date || !data.end_date) return true;
      const startDate = new Date(data.start_date);
      const endDate = new Date(data.end_date);
      return endDate >= startDate;
    },
    {
      message: 'End date must be after start date',
      path: ['end_date'],
    }
  );

// Family schemas
export const createFamilySchema = z.object({
  name: nameSchema,
  description: z.string().optional(),
});

export const inviteFamilyMemberSchema = z.object({
  family_id: z.string().min(1, 'Family selection is required'),
  email: emailSchema,
});

// User schemas
export const userProfileSchema = z.object({
  name: nameSchema,
  email: emailSchema,
  phone: phoneSchema,
  bio: z.string().optional(),
  location: z.string().optional(),
});

export const notificationPreferencesSchema = z.object({
  emailNotifications: z.boolean(),
  pushNotifications: z.boolean(),
  tripUpdates: z.boolean(),
  familyInvitations: z.boolean(),
  itineraryChanges: z.boolean(),
  marketingEmails: z.boolean(),
});

export const privacySettingsSchema = z.object({
  profileVisibility: z.enum(['public', 'family', 'private']),
  showLocation: z.boolean(),
  allowFamilyInvites: z.boolean(),
  shareLocation: z.boolean(),
});

// Login schema
export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Password is required'),
});

// Registration schema
export const registerSchema = z.object({
  email: emailSchema,
  password: passwordSchema,
  full_name: nameSchema,
  phone_number: phoneSchema,
  date_of_birth: z.string().optional(),
  emergency_contact_name: z.string().optional(),
  emergency_contact_phone: phoneSchema,
});

// Validate helper function
export const validateForm = <T>(
  schema: z.ZodType<T>,
  data: any
): { isValid: boolean; errors: Record<string, string> } => {
  try {
    schema.parse(data);
    return { isValid: true, errors: {} };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const formattedErrors: Record<string, string> = {};
      error.errors.forEach((err) => {
        const field = err.path.join('.') || 'general';
        formattedErrors[field] = err.message;
      });
      return { isValid: false, errors: formattedErrors };
    }
    return {
      isValid: false,
      errors: { general: 'Validation failed. Please check your inputs.' },
    };
  }
};
