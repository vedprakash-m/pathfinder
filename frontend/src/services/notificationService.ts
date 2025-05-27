import { apiService } from './api';
import websocketService from './websocket';
import { ApiResponse } from '@/types';

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  read: boolean;
  action_url?: string;
  created_at: string;
  related_entity_id?: string;
  related_entity_type?: string;
}

export interface NotificationFilters {
  read?: boolean;
  type?: string;
  start_date?: string;
  end_date?: string;
}

export interface NotificationSettings {
  email_notifications: boolean;
  push_notifications: boolean;
  trip_updates: boolean;
  family_updates: boolean;
  marketing: boolean;
}

export class NotificationService {
  private onNewNotificationCallbacks: ((notification: Notification) => void)[] = [];
  
  constructor() {
    // Set up WebSocket listeners
    websocketService.on<Notification>('notification', (notification) => {
      this.handleNewNotification(notification);
    });
  }
  
  // Get all notifications for the current user
  async getNotifications(filters?: NotificationFilters): Promise<ApiResponse<Notification[]>> {
    let queryParams = '';
    
    if (filters) {
      const params = new URLSearchParams();
      
      if (filters.read !== undefined) {
        params.append('read', filters.read.toString());
      }
      if (filters.type) {
        params.append('type', filters.type);
      }
      if (filters.start_date) {
        params.append('start_date', filters.start_date);
      }
      if (filters.end_date) {
        params.append('end_date', filters.end_date);
      }
      
      queryParams = `?${params.toString()}`;
    }
    
    return apiService.get<Notification[]>(`/notifications${queryParams}`);
  }
  
  // Mark a notification as read
  async markAsRead(notificationId: string): Promise<ApiResponse<Notification>> {
    return apiService.patch<Notification>(`/notifications/${notificationId}/read`, { read: true });
  }
  
  // Mark all notifications as read
  async markAllAsRead(): Promise<ApiResponse<void>> {
    return apiService.post<void>('/notifications/mark-all-read');
  }
  
  // Delete a notification
  async deleteNotification(notificationId: string): Promise<ApiResponse<void>> {
    return apiService.delete<void>(`/notifications/${notificationId}`);
  }
  
  // Get notification settings
  async getNotificationSettings(): Promise<ApiResponse<NotificationSettings>> {
    return apiService.get<NotificationSettings>('/notifications/settings');
  }
  
  // Update notification settings
  async updateNotificationSettings(settings: Partial<NotificationSettings>): Promise<ApiResponse<NotificationSettings>> {
    return apiService.patch<NotificationSettings>('/notifications/settings', settings);
  }
  
  // Get unread count
  async getUnreadCount(): Promise<ApiResponse<{ count: number }>> {
    return apiService.get<{ count: number }>('/notifications/unread-count');
  }
  
  // Subscribe to push notifications (browser)
  async subscribeToPushNotifications(): Promise<boolean> {
    try {
      const sw = await navigator.serviceWorker.ready;
      
      // Request notification permission
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        return false;
      }
      
      // Subscribe to push notifications
      const subscription = await sw.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(
          import.meta.env.VITE_VAPID_PUBLIC_KEY as string
        ),
      });
      
      // Send subscription to server
      await apiService.post('/notifications/subscribe', {
        subscription: JSON.stringify(subscription),
      });
      
      return true;
    } catch (error) {
      console.error('Error subscribing to push notifications:', error);
      return false;
    }
  }
  
  // Unsubscribe from push notifications
  async unsubscribeFromPushNotifications(): Promise<boolean> {
    try {
      const sw = await navigator.serviceWorker.ready;
      const subscription = await sw.pushManager.getSubscription();
      
      if (subscription) {
        // Unsubscribe from push manager
        await subscription.unsubscribe();
        
        // Unsubscribe on server
        await apiService.post('/notifications/unsubscribe', {
          subscription: JSON.stringify(subscription),
        });
      }
      
      return true;
    } catch (error) {
      console.error('Error unsubscribing from push notifications:', error);
      return false;
    }
  }
  
  // Register notification callback
  onNewNotification(callback: (notification: Notification) => void): () => void {
    this.onNewNotificationCallbacks.push(callback);
    
    // Return unsubscribe function
    return () => {
      this.onNewNotificationCallbacks = this.onNewNotificationCallbacks.filter(cb => cb !== callback);
    };
  }
  
  // Handle new notification from WebSocket
  private handleNewNotification(notification: Notification): void {
    // Trigger callbacks
    this.onNewNotificationCallbacks.forEach(callback => {
      try {
        callback(notification);
      } catch (error) {
        console.error('Error in notification callback:', error);
      }
    });
    
    // Display browser notification if supported and permission granted
    if ('Notification' in window && Notification.permission === 'granted') {
      const browserNotification = new Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.ico',
        tag: notification.id,
      });
      
      // Handle click on notification
      browserNotification.onclick = () => {
        window.focus();
        if (notification.action_url) {
          window.location.href = notification.action_url;
        }
        browserNotification.close();
      };
    }
  }
  
  // Helper method to convert base64 to Uint8Array for VAPID key
  private urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');
    
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    
    return outputArray;
  }
}

const notificationService = new NotificationService();
export default notificationService;
