import React from 'react';
import { 
  Calendar, 
  MapPin, 
  Clock, 
  DollarSign, 
  Users, 
  AlertCircle,
  CheckCircle,
  Sun,
  Utensils,
  Activity
} from 'lucide-react';

interface DayActivity {
  time: string;
  title: string;
  description: string;
  location: string;
  duration: string;
  cost_per_person?: number;
  category: 'breakfast' | 'lunch' | 'dinner' | 'activity' | 'travel' | 'accommodation';
  notes?: string;
}

interface DayItinerary {
  day: number;
  date: string;
  title: string;
  activities: DayActivity[];
  total_cost_per_person?: number;
  weather?: string;
  logistics_notes?: string[];
}

interface BudgetBreakdown {
  accommodation: number;
  meals: number;
  activities: number;
  transportation: number;
  miscellaneous: number;
  total_per_person: number;
  total_per_family: number;
}

interface Itinerary {
  overview: {
    destination: string;
    duration: number;
    total_participants: number;
    family_count: number;
    estimated_cost_per_person: number;
    estimated_cost_per_family: number;
    best_time_to_visit: string;
    weather_info: string;
    group_coordination_tips?: string[];
    travel_tips?: string[];
  };
  daily_itinerary: DayItinerary[];
  budget_summary: BudgetBreakdown;
  logistics?: {
    transportation?: string[];
    accommodation?: string[];
    communication?: string[];
  };
  packing_suggestions?: {
    essentials?: string[];
    optional?: string[];
    family_specific?: string[];
  };
  important_notes?: string[];
  emergency_contacts?: Array<{
    name: string;
    phone: string;
    type: string;
  }>;
  alternative_plans?: {
    rainy_day?: string[];
    indoor_activities?: string[];
  };
  multi_family_considerations?: {
    meeting_points?: string[];
    communication_plan?: string;
    cost_splitting?: string;
  };
}

interface ItineraryViewProps {
  itinerary: Itinerary;
  className?: string;
  onPrint?: () => void;
  onExport?: () => void;
}

export const ItineraryView: React.FC<ItineraryViewProps> = ({
  itinerary,
  className = '',
  onPrint,
  onExport
}) => {
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'breakfast':
      case 'lunch':
      case 'dinner':
        return <Utensils className="h-4 w-4" />;
      case 'activity':
        return <Activity className="h-4 w-4" />;
      case 'travel':
        return <MapPin className="h-4 w-4" />;
      case 'accommodation':
        return <CheckCircle className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'breakfast':
      case 'lunch':
      case 'dinner':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'activity':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'travel':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'accommodation':
        return 'bg-green-50 text-green-700 border-green-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className={`space-y-8 ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold">{itinerary.overview.destination}</h1>
          <div className="flex items-center space-x-2">
            {onPrint && (
              <button
                onClick={onPrint}
                className="px-4 py-2 bg-white text-blue-600 rounded hover:bg-gray-100 transition-colors text-sm font-medium"
              >
                Print
              </button>
            )}
            {onExport && (
              <button
                onClick={onExport}
                className="px-4 py-2 bg-white text-blue-600 rounded hover:bg-gray-100 transition-colors text-sm font-medium"
              >
                Export
              </button>
            )}
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <Calendar className="h-5 w-5" />
            <div>
              <p className="font-semibold">{itinerary.overview.duration} Days</p>
              <p className="text-blue-100">Duration</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Users className="h-5 w-5" />
            <div>
              <p className="font-semibold">{itinerary.overview.total_participants} People</p>
              <p className="text-blue-100">{itinerary.overview.family_count} Families</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <DollarSign className="h-5 w-5" />
            <div>
              <p className="font-semibold">${itinerary.overview.estimated_cost_per_person.toLocaleString()}</p>
              <p className="text-blue-100">Per Person</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Sun className="h-5 w-5" />
            <div>
              <p className="font-semibold">{itinerary.overview.best_time_to_visit}</p>
              <p className="text-blue-100">Best Time</p>
            </div>
          </div>
        </div>
        
        {itinerary.overview.weather_info && (
          <p className="mt-4 text-blue-100">{itinerary.overview.weather_info}</p>
        )}
      </div>

      {/* Group Coordination Tips */}
      {itinerary.overview.group_coordination_tips && itinerary.overview.group_coordination_tips.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="font-semibold text-yellow-900 mb-2 flex items-center space-x-2">
            <AlertCircle className="h-5 w-5" />
            <span>Multi-Family Coordination Tips</span>
          </h3>
          <ul className="list-disc list-inside space-y-1 text-yellow-800 text-sm">
            {itinerary.overview.group_coordination_tips.map((tip, index) => (
              <li key={index}>{tip}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Daily Itinerary */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
          <Calendar className="h-6 w-6 text-blue-500" />
          <span>Daily Itinerary</span>
        </h2>
        
        {itinerary.daily_itinerary.map((day) => (
          <div key={day.day} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            {/* Day Header */}
            <div className="bg-gray-50 border-b border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Day {day.day}: {day.title}
                  </h3>
                  <p className="text-sm text-gray-600">{day.date}</p>
                </div>
                <div className="text-right">
                  {day.total_cost_per_person && (
                    <p className="text-sm font-medium text-gray-900">
                      ${day.total_cost_per_person.toLocaleString()} per person
                    </p>
                  )}
                  {day.weather && (
                    <p className="text-sm text-gray-600">{day.weather}</p>
                  )}
                </div>
              </div>
            </div>
            
            {/* Activities */}
            <div className="p-4 space-y-4">
              {day.activities.map((activity, index) => (
                <div key={index} className="flex items-start space-x-4">
                  <div className="flex-shrink-0 w-16 text-sm font-medium text-gray-600">
                    {activity.time}
                  </div>
                  <div className={`flex-1 border rounded-lg p-3 ${getCategoryColor(activity.category)}`}>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {getCategoryIcon(activity.category)}
                        <h4 className="font-semibold">{activity.title}</h4>
                      </div>
                      {activity.cost_per_person && (
                        <span className="text-sm font-medium">
                          ${activity.cost_per_person}/person
                        </span>
                      )}
                    </div>
                    <p className="text-sm mb-2">{activity.description}</p>
                    <div className="flex items-center space-x-4 text-xs">
                      <span className="flex items-center space-x-1">
                        <MapPin className="h-3 w-3" />
                        <span>{activity.location}</span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <Clock className="h-3 w-3" />
                        <span>{activity.duration}</span>
                      </span>
                    </div>
                    {activity.notes && (
                      <p className="text-xs mt-2 italic">{activity.notes}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            {/* Logistics Notes */}
            {day.logistics_notes && day.logistics_notes.length > 0 && (
              <div className="bg-blue-50 border-t border-blue-100 p-4">
                <p className="text-sm font-medium text-blue-900 mb-1">Logistics:</p>
                <ul className="list-disc list-inside space-y-1 text-sm text-blue-800">
                  {day.logistics_notes.map((note, index) => (
                    <li key={index}>{note}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Budget Summary */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
          <DollarSign className="h-6 w-6 text-green-500" />
          <span>Budget Breakdown</span>
        </h2>
        
        <div className="grid md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-gray-200">
              <span className="text-gray-700">Accommodation</span>
              <span className="font-medium">${itinerary.budget_summary.accommodation.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-200">
              <span className="text-gray-700">Meals</span>
              <span className="font-medium">${itinerary.budget_summary.meals.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-200">
              <span className="text-gray-700">Activities</span>
              <span className="font-medium">${itinerary.budget_summary.activities.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-200">
              <span className="text-gray-700">Transportation</span>
              <span className="font-medium">${itinerary.budget_summary.transportation.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-200">
              <span className="text-gray-700">Miscellaneous</span>
              <span className="font-medium">${itinerary.budget_summary.miscellaneous.toLocaleString()}</span>
            </div>
          </div>
          
          <div className="bg-green-50 rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between text-lg">
              <span className="font-semibold text-green-900">Per Person</span>
              <span className="font-bold text-green-700">
                ${itinerary.budget_summary.total_per_person.toLocaleString()}
              </span>
            </div>
            <div className="flex items-center justify-between text-lg">
              <span className="font-semibold text-green-900">Per Family (avg)</span>
              <span className="font-bold text-green-700">
                ${itinerary.budget_summary.total_per_family.toLocaleString()}
              </span>
            </div>
            {itinerary.multi_family_considerations?.cost_splitting && (
              <p className="text-sm text-green-800 mt-2">
                {itinerary.multi_family_considerations.cost_splitting}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Additional Information Grid */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Packing Suggestions */}
        {itinerary.packing_suggestions && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Packing Suggestions</h3>
            {itinerary.packing_suggestions.essentials && (
              <div className="mb-3">
                <p className="text-sm font-medium text-gray-700 mb-1">Essentials:</p>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {itinerary.packing_suggestions.essentials.slice(0, 5).map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Important Notes */}
        {itinerary.important_notes && itinerary.important_notes.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h3 className="font-semibold text-red-900 mb-3 flex items-center space-x-2">
              <AlertCircle className="h-5 w-5" />
              <span>Important Notes</span>
            </h3>
            <ul className="list-disc list-inside text-sm text-red-800 space-y-1">
              {itinerary.important_notes.map((note, index) => (
                <li key={index}>{note}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Alternative Plans */}
        {itinerary.alternative_plans && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-semibold text-blue-900 mb-3">Backup Plans</h3>
            {itinerary.alternative_plans.rainy_day && (
              <div className="mb-3">
                <p className="text-sm font-medium text-blue-700 mb-1">Rainy Day Options:</p>
                <ul className="list-disc list-inside text-sm text-blue-600 space-y-1">
                  {itinerary.alternative_plans.rainy_day.slice(0, 3).map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Emergency Contacts */}
        {itinerary.emergency_contacts && itinerary.emergency_contacts.length > 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Emergency Contacts</h3>
            <div className="space-y-2">
              {itinerary.emergency_contacts.map((contact, index) => (
                <div key={index} className="text-sm">
                  <p className="font-medium text-gray-900">{contact.name}</p>
                  <p className="text-gray-600">{contact.type}: {contact.phone}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ItineraryView;
