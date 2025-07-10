import React from 'react';
import { Link } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardPreview,
  Badge,
  Button,
  Title3,
  Body1,
  Caption1,
} from '@fluentui/react-components';
import {
  CalendarIcon,
  MapPinIcon,
  UsersIcon,
} from '@heroicons/react/24/outline';
import type { Trip, TripStatus } from '@/types';

interface TripCardProps {
  trip: Trip;
  onJoin?: (tripId: string) => void;
  onLeave?: (tripId: string) => void;
  className?: string;
}

const StatusBadge: React.FC<{ status: TripStatus }> = ({ status }) => {
  const getStatusColor = (status: TripStatus) => {
    switch (status) {
      case 'planning':
        return 'warning';
      case 'confirmed':
        return 'success';
      case 'completed':
        return 'informative';
      case 'cancelled':
        return 'danger';
      default:
        return 'subtle';
    }
  };

  return (
    <Badge color={getStatusColor(status)} className="capitalize">
      {status}
    </Badge>
  );
};

export const TripCard: React.FC<TripCardProps> = ({ 
  trip, 
  onJoin, 
  onLeave, 
  className = '' 
}) => {
  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getDuration = () => {
    if (!trip.start_date || !trip.end_date) return '';
    const start = new Date(trip.start_date);
    const end = new Date(trip.end_date);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return `${diffDays} day${diffDays !== 1 ? 's' : ''}`;
  };

  return (
    <Card className={`w-full max-w-sm ${className}`}>
      <CardHeader
        header={
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <Link to={`/trips/${trip.id}`} className="hover:underline">
                <Title3>{trip.title}</Title3>
              </Link>
              <StatusBadge status={trip.status} />
            </div>
          </div>
        }
        description={
          <Body1 className="text-gray-600 mt-2">
            {trip.description || 'No description provided'}
          </Body1>
        }
      />

      <CardPreview className="p-4">
        <div className="space-y-3">
          {/* Destination */}
          <div className="flex items-center gap-2">
            <MapPinIcon className="w-4 h-4 text-gray-500" />
            <Caption1 className="text-gray-700">
              {trip.destination}
            </Caption1>
          </div>

          {/* Dates */}
          {trip.start_date && (
            <div className="flex items-center gap-2">
              <CalendarIcon className="w-4 h-4 text-gray-500" />
              <Caption1 className="text-gray-700">
                {formatDate(trip.start_date)}
                {trip.end_date && ` - ${formatDate(trip.end_date)}`}
                {getDuration() && ` (${getDuration()})`}
              </Caption1>
            </div>
          )}

          {/* Participants */}
          <div className="flex items-center gap-2">
            <UsersIcon className="w-4 h-4 text-gray-500" />
            <Caption1 className="text-gray-700">
              {trip.family_count || 0} families
              {trip.participants && ` / ${trip.participants.length} participants`}
            </Caption1>
          </div>

          {/* Budget */}
          {trip.budget_total && (
            <div className="flex items-center justify-between">
              <Caption1 className="text-gray-700">Budget:</Caption1>
              <Caption1 className="font-semibold">
                ${trip.budget_total.toLocaleString()}
              </Caption1>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 mt-4">
          <Link to={`/trips/${trip.id}`}>
            <Button appearance="primary" size="small">
              View Details
            </Button>
          </Link>
          
          {onJoin && trip.status === 'planning' && (
            <Button 
              appearance="outline" 
              size="small"
              onClick={() => onJoin(trip.id)}
            >
              Join Trip
            </Button>
          )}
          
          {onLeave && (
            <Button 
              appearance="subtle" 
              size="small"
              onClick={() => onLeave(trip.id)}
            >
              Leave
            </Button>
          )}
        </div>
      </CardPreview>
    </Card>
  );
};

export default TripCard;
