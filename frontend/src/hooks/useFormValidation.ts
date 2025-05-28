import { useState } from 'react';
import { z } from 'zod';

/**
 * Validate form data using Zod schema
 */
const validateForm = <T>(schema: z.ZodType<T>, data: Partial<T>) => {
  try {
    schema.parse(data);
    return { isValid: true, errors: {} };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errors: Record<string, string> = {};
      error.errors.forEach((err) => {
        const field = err.path.join('.');
        errors[field] = err.message;
      });
      return { isValid: false, errors };
    }
    return { isValid: false, errors: { general: 'Validation failed' } };
  }
};

/**
 * Custom hook for form validation using Zod schemas
 */
export function useFormValidation<T>(schema: z.ZodType<T>, initialData: Partial<T>) {
  const [formData, setFormData] = useState<Partial<T>>(initialData);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  /**
   * Update form data and clear relevant errors
   */
  const updateFormData = (updates: Partial<T>) => {
    setFormData((prev) => ({ ...prev, ...updates }));
    
    // Clear errors for updated fields
    const newErrors = { ...errors };
    Object.keys(updates).forEach((key) => {
      delete newErrors[key];
    });
    setErrors(newErrors);
    
    // Mark fields as touched
    const newTouched = { ...touched };
    Object.keys(updates).forEach((key) => {
      newTouched[key] = true;
    });
    setTouched(newTouched);
  };

  /**
   * Handle blur event for a field to mark it as touched
   */
  const handleBlur = (field: keyof T) => {
    setTouched((prev) => ({
      ...prev,
      [field]: true,
    }));
    
    // Validate individual field on blur
    validateField(field as string);
  };

  /**
   * Validate a single field
   */
  const validateField = (field: string) => {
    try {
      // Try to validate the entire form and extract field-specific errors
      schema.parse(formData);
      
      // Clear error if validation passes
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
      
      return true;
    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors = error.errors.filter((err: any) => 
          err.path[0] === field || err.path.join('.') === field
        );
        
        if (fieldErrors.length > 0) {
          setErrors((prev) => ({
            ...prev,
            [field]: fieldErrors[0].message,
          }));
          return false;
        }
      }
      return true;
    }
  };

  /**
   * Validate the entire form
   */
  const validateAll = (): boolean => {
    const { isValid, errors: validationErrors } = validateForm(schema, formData);
    setErrors(validationErrors);
    
    // Mark all fields as touched if validation fails
    if (!isValid) {
      const allTouched: Record<string, boolean> = {};
      Object.keys(validationErrors).forEach((key) => {
        allTouched[key] = true;
      });
      setTouched((prev) => ({ ...prev, ...allTouched }));
    }
    
    return isValid;
  };

  /**
   * Reset form to initial data and clear errors
   */
  const resetForm = () => {
    setFormData(initialData);
    setErrors({});
    setTouched({});
  };

  /**
   * Get validation state for a field
   */
  const getFieldState = (field: keyof T) => {
    const isTouched = !!touched[field as string];
    const hasError = !!errors[field as string];
    
    return {
      error: isTouched && hasError ? errors[field as string] : undefined,
      validationState: isTouched && hasError ? 'error' as const : 'none' as const,
    };
  };

  return {
    formData,
    errors,
    touched,
    updateFormData,
    handleBlur,
    validateField,
    validateAll,
    resetForm,
    getFieldState,
  };
}
