import { useState } from 'react';
import { z } from 'zod';
import { validateForm } from '@/utils/validation';

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
      // Create an object with just the field to validate
      const fieldData = { [field]: formData[field as keyof T] };
      
      // Extract the sub-schema for just this field if possible
      const fieldSchema = schema.shape?.[field as keyof z.ZodTypeAny] || schema;
      
      // Try to parse (validate) just this field
      fieldSchema.parse(formData[field as keyof T]);
      
      // Clear error if validation passes
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
      
      return true;
    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors = error.errors.filter((err) => 
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
