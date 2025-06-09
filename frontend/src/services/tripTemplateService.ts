import { TripType } from '../components/onboarding/OnboardingFlow';

export interface TripTemplate {
  id: string;
  type: TripType;
  title: string;
  description: string;
  duration: string;
  location: string;
  groupSize: string;
  budget: string;
  highlights: string[];
  itinerary: ItineraryDay[];
  tags: string[];
  imageUrl: string;
  difficulty: 'Easy' | 'Moderate' | 'Challenging';
  bestSeason: string[];
}

export interface ItineraryDay {
  day: number;
  title: string;
  activities: Activity[];
  meals: MealRecommendation[];
  accommodation?: string;
  notes?: string;
}

export interface Activity {
  id: string;
  name: string;
  description: string;
  duration: string;
  type: 'sightseeing' | 'adventure' | 'cultural' | 'relaxation' | 'dining' | 'shopping';
  location: string;
  cost: string;
  ageRecommendation: string;
  tags: string[];
}

export interface MealRecommendation {
  type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  name: string;
  location: string;
  cost: string;
  cuisine: string;
  description: string;
}

// Pre-built trip templates
export const tripTemplates: TripTemplate[] = [
  // Weekend Getaway Templates
  {
    id: 'weekend-napa-valley',
    type: 'weekend-getaway',
    title: 'Napa Valley Family Weekend',
    description: 'A relaxing weekend exploring California wine country with family-friendly activities and beautiful scenery.',
    duration: '2-3 days',
    location: 'Napa Valley, California',
    groupSize: '4-6 people',
    budget: '$800-1200 per family',
    difficulty: 'Easy',
    bestSeason: ['Spring', 'Summer', 'Fall'],
    highlights: [
      'Family-friendly wineries with activities for kids',
      'Scenic hot air balloon rides',
      'Farm-to-table dining experiences',
      'Beautiful vineyard landscapes'
    ],
    tags: ['wine country', 'scenic', 'relaxing', 'family-friendly'],
    imageUrl: '/images/napa-valley.jpg',
    itinerary: [
      {
        day: 1,
        title: 'Arrival & Valley Exploration',
        activities: [
          {
            id: 'checkin',
            name: 'Hotel Check-in',
            description: 'Settle into family-friendly accommodations in downtown Napa',
            duration: '30 minutes',
            type: 'relaxation',
            location: 'Downtown Napa',
            cost: '$0',
            ageRecommendation: 'All ages',
            tags: ['accommodation']
          },
          {
            id: 'oxbow-market',
            name: 'Oxbow Public Market',
            description: 'Local food market with diverse vendors and family-friendly atmosphere',
            duration: '2 hours',
            type: 'dining',
            location: '610 1st St, Napa',
            cost: '$40-60 per person',
            ageRecommendation: 'All ages',
            tags: ['food', 'local', 'market']
          }
        ],
        meals: [
          {
            type: 'lunch',
            name: 'Oxbow Public Market',
            location: '610 1st St, Napa',
            cost: '$15-25 per person',
            cuisine: 'Various',
            description: 'Artisanal food vendors with options for everyone'
          },
          {
            type: 'dinner',
            name: 'Bounty Hunter Wine Bar',
            location: '975 1st St, Napa',
            cost: '$30-45 per person',
            cuisine: 'American',
            description: 'Family-friendly restaurant with great wine selection and kid-friendly menu'
          }
        ]
      },
      {
        day: 2,
        title: 'Winery & Outdoor Adventures',
        activities: [
          {
            id: 'family-winery',
            name: 'Castello di Amorosa',
            description: 'Medieval castle winery with tours and activities for children',
            duration: '3 hours',
            type: 'cultural',
            location: '4045 St Helena Hwy, Calistoga',
            cost: '$40-55 per adult, $25 per child',
            ageRecommendation: 'All ages',
            tags: ['winery', 'castle', 'family-friendly', 'educational']
          },
          {
            id: 'balloon-ride',
            name: 'Hot Air Balloon Experience',
            description: 'Scenic balloon ride over Napa Valley (weather permitting)',
            duration: '4 hours total',
            type: 'adventure',
            location: 'Various launch sites',
            cost: '$200-250 per person',
            ageRecommendation: '8+ years',
            tags: ['adventure', 'scenic', 'memorable']
          }
        ],
        meals: [
          {
            type: 'breakfast',
            name: 'Model Bakery',
            location: '1357 Main St, St Helena',
            cost: '$8-15 per person',
            cuisine: 'Bakery',
            description: 'Famous for English muffins and pastries'
          },
          {
            type: 'lunch',
            name: 'Castello di Amorosa Café',
            location: 'At the winery',
            cost: '$20-30 per person',
            cuisine: 'Italian',
            description: 'Castle dining with Italian specialties'
          }
        ]
      }
    ]
  },

  // Family Vacation Templates
  {
    id: 'family-yellowstone',
    type: 'family-vacation',
    title: 'Yellowstone National Park Family Adventure',
    description: 'A week-long exploration of America\'s first national park with activities for all ages and unforgettable wildlife experiences.',
    duration: '7 days',
    location: 'Yellowstone National Park, Wyoming',
    groupSize: '4-10 people',
    budget: '$2000-3500 per family',
    difficulty: 'Moderate',
    bestSeason: ['Summer', 'Early Fall'],
    highlights: [
      'Old Faithful and geothermal wonders',
      'Wildlife viewing opportunities',
      'Junior Ranger program for kids',
      'Scenic drives and easy hiking trails',
      'Educational visitor centers'
    ],
    tags: ['national park', 'wildlife', 'educational', 'outdoor', 'family-bonding'],
    imageUrl: '/images/yellowstone.jpg',
    itinerary: [
      {
        day: 1,
        title: 'Arrival & Old Faithful Area',
        activities: [
          {
            id: 'old-faithful',
            name: 'Old Faithful Visitor Center',
            description: 'Learn about geothermal features and watch the famous geyser erupt',
            duration: '3 hours',
            type: 'sightseeing',
            location: 'Old Faithful Area',
            cost: 'Park entrance fee',
            ageRecommendation: 'All ages',
            tags: ['geyser', 'educational', 'iconic']
          },
          {
            id: 'junior-ranger',
            name: 'Junior Ranger Program Sign-up',
            description: 'Get kids started on earning their Junior Ranger badge',
            duration: '30 minutes',
            type: 'cultural',
            location: 'Visitor Center',
            cost: 'Free',
            ageRecommendation: '5-12 years',
            tags: ['educational', 'kids', 'program']
          }
        ],
        meals: [
          {
            type: 'lunch',
            name: 'Old Faithful Inn Dining Room',
            location: 'Old Faithful Inn',
            cost: '$25-40 per person',
            cuisine: 'American',
            description: 'Historic lodge dining with rustic atmosphere'
          }
        ],
        accommodation: 'Old Faithful Inn or nearby cabin'
      }
      // Additional days would be added here...
    ]
  },

  // Adventure Trip Templates
  {
    id: 'adventure-moab',
    type: 'adventure-trip',
    title: 'Moab Desert Adventure',
    description: 'An action-packed adventure in Utah\'s red rock country with hiking, biking, and outdoor challenges for active families.',
    duration: '5 days',
    location: 'Moab, Utah',
    groupSize: '2-8 people',
    budget: '$1500-2500 per family',
    difficulty: 'Challenging',
    bestSeason: ['Spring', 'Fall'],
    highlights: [
      'Arches and Canyonlands National Parks',
      'Mountain biking on world-famous trails',
      'Rock climbing and canyoneering',
      'Colorado River rafting',
      'Stargazing in dark skies'
    ],
    tags: ['adventure', 'hiking', 'biking', 'rafting', 'national parks'],
    imageUrl: '/images/moab.jpg',
    itinerary: [
      {
        day: 1,
        title: 'Arches National Park',
        activities: [
          {
            id: 'delicate-arch',
            name: 'Delicate Arch Hike',
            description: 'Iconic 3-mile round trip hike to Utah\'s most famous landmark',
            duration: '3 hours',
            type: 'adventure',
            location: 'Arches National Park',
            cost: 'Park entrance fee',
            ageRecommendation: '8+ years',
            tags: ['hiking', 'iconic', 'moderate difficulty']
          },
          {
            id: 'windows-section',
            name: 'Windows Section',
            description: 'Easy walks to see multiple arches in one area',
            duration: '2 hours',
            type: 'sightseeing',
            location: 'Arches National Park',
            cost: 'Park entrance fee',
            ageRecommendation: 'All ages',
            tags: ['easy', 'family-friendly', 'arches']
          }
        ],
        meals: [
          {
            type: 'dinner',
            name: 'Pasta Jay\'s',
            location: '4 N Main St, Moab',
            cost: '$15-25 per person',
            cuisine: 'Italian',
            description: 'Local favorite with hearty portions for hungry adventurers'
          }
        ]
      }
      // Additional days would be added here...
    ]
  },

  // Additional Weekend Getaway Templates
  {
    id: 'weekend-asheville',
    type: 'weekend-getaway',
    title: 'Asheville Mountain Retreat',
    description: 'A scenic weekend in the Blue Ridge Mountains with craft breweries, outdoor activities, and family fun.',
    duration: '2-3 days',
    location: 'Asheville, North Carolina',
    groupSize: '4-8 people',
    budget: '$600-900 per family',
    difficulty: 'Easy',
    bestSeason: ['Spring', 'Summer', 'Fall'],
    highlights: [
      'Blue Ridge Parkway scenic drives',
      'Family-friendly breweries with outdoor spaces',
      'Easy hiking trails and waterfalls',
      'Historic Biltmore Estate tours'
    ],
    tags: ['mountains', 'breweries', 'scenic drives', 'family-friendly'],
    imageUrl: '/images/asheville.jpg',
    itinerary: [
      {
        day: 1,
        title: 'Downtown & Brewery Tour',
        activities: [
          {
            id: 'downtown-walk',
            name: 'Downtown Asheville Walk',
            description: 'Explore the vibrant downtown area with street art and local shops',
            duration: '2 hours',
            type: 'cultural',
            location: 'Downtown Asheville',
            cost: 'Free',
            ageRecommendation: 'All ages',
            tags: ['walking', 'culture', 'free']
          }
        ],
        meals: [
          {
            type: 'lunch',
            name: 'Highland Brewing Company',
            location: '12 Old Charlotte Hwy',
            cost: '$15-25 per person',
            cuisine: 'American',
            description: 'Family-friendly brewery with outdoor seating and kids menu'
          }
        ]
      }
    ]
  },

  // Additional Family Vacation Templates
  {
    id: 'family-disney-world',
    type: 'family-vacation',
    title: 'Walt Disney World Magic',
    description: 'The ultimate family vacation at the most magical place on earth with parks, resorts, and unforgettable memories.',
    duration: '5-7 days',
    location: 'Orlando, Florida',
    groupSize: '4-12 people',
    budget: '$3000-5000 per family',
    difficulty: 'Easy',
    bestSeason: ['Fall', 'Winter', 'Spring'],
    highlights: [
      'Four theme parks with rides for all ages',
      'Character dining experiences',
      'Resort pools and activities',
      'Disney Springs entertainment district',
      'Memory Maker photo package'
    ],
    tags: ['theme parks', 'characters', 'magical', 'all ages'],
    imageUrl: '/images/disney-world.jpg',
    itinerary: [
      {
        day: 1,
        title: 'Magic Kingdom Adventure',
        activities: [
          {
            id: 'magic-kingdom',
            name: 'Magic Kingdom Park',
            description: 'Classic Disney experience with iconic attractions and character meet-and-greets',
            duration: '10 hours',
            type: 'sightseeing',
            location: 'Magic Kingdom',
            cost: 'Park ticket included',
            ageRecommendation: 'All ages',
            tags: ['theme park', 'rides', 'characters']
          }
        ],
        meals: [
          {
            type: 'dinner',
            name: 'Be Our Guest Restaurant',
            location: 'Magic Kingdom - Fantasyland',
            cost: '$60-75 per adult, $35-40 per child',
            cuisine: 'French',
            description: 'Themed dining in Beast\'s castle with character interactions'
          }
        ]
      }
    ]
  },

  // Additional Adventure Trip Templates
  {
    id: 'adventure-glacier',
    type: 'adventure-trip',
    title: 'Glacier National Park Expedition',
    description: 'An epic adventure through pristine wilderness with challenging hikes, pristine lakes, and wildlife encounters.',
    duration: '6 days',
    location: 'Glacier National Park, Montana',
    groupSize: '2-6 people',
    budget: '$1800-2800 per family',
    difficulty: 'Challenging',
    bestSeason: ['Summer', 'Early Fall'],
    highlights: [
      'Going-to-the-Sun Road scenic drive',
      'Challenging backcountry hiking trails',
      'Pristine alpine lakes and glaciers',
      'Wildlife viewing opportunities',
      'Photography workshops'
    ],
    tags: ['wilderness', 'challenging hikes', 'photography', 'wildlife'],
    imageUrl: '/images/glacier.jpg',
    itinerary: [
      {
        day: 1,
        title: 'Going-to-the-Sun Road',
        activities: [
          {
            id: 'sun-road',
            name: 'Going-to-the-Sun Road Drive',
            description: 'Spectacular mountain road with breathtaking views and photo opportunities',
            duration: '6 hours',
            type: 'sightseeing',
            location: 'Glacier National Park',
            cost: 'Park entrance fee',
            ageRecommendation: 'All ages',
            tags: ['scenic drive', 'photography', 'mountains']
          }
        ],
        meals: [
          {
            type: 'lunch',
            name: 'Logan Pass Visitor Center',
            location: 'Logan Pass',
            cost: '$12-18 per person',
            cuisine: 'Grab & Go',
            description: 'Light meals with spectacular mountain views'
          }
        ]
      }
    ]
  }
];

export class TripTemplateService {
  static getTemplatesByType(type: TripType): TripTemplate[] {
    return tripTemplates.filter(template => template.type === type);
  }

  static getTemplateById(id: string): TripTemplate | undefined {
    return tripTemplates.find(template => template.id === id);
  }

  static getRandomTemplate(type: TripType): TripTemplate | undefined {
    const templates = this.getTemplatesByType(type);
    if (templates.length === 0) return undefined;
    
    const randomIndex = Math.floor(Math.random() * templates.length);
    return templates[randomIndex];
  }

  static getAllTemplates(): TripTemplate[] {
    return tripTemplates;
  }

  static searchTemplates(query: string): TripTemplate[] {
    const searchTerm = query.toLowerCase();
    return tripTemplates.filter(template => 
      template.title.toLowerCase().includes(searchTerm) ||
      template.description.toLowerCase().includes(searchTerm) ||
      template.location.toLowerCase().includes(searchTerm) ||
      template.tags.some(tag => tag.toLowerCase().includes(searchTerm))
    );
  }

  static getTemplatesByBudget(maxBudget: number): TripTemplate[] {
    return tripTemplates.filter(template => {
      // Extract budget numbers from strings like "$800-1200 per family"
      const budgetMatch = template.budget.match(/\$(\d+)-?(\d+)?/);
      if (!budgetMatch) return false;
      
      const minTemplateBudget = parseInt(budgetMatch[1]);
      
      // Template fits budget if its minimum cost is within the provided budget
      return minTemplateBudget <= maxBudget;
    });
  }

  static getTemplatesByDifficulty(difficulty: TripTemplate['difficulty']): TripTemplate[] {
    return tripTemplates.filter(template => template.difficulty === difficulty);
  }

  static getTemplatesBySeason(season: string): TripTemplate[] {
    return tripTemplates.filter(template => 
      template.bestSeason.includes(season)
    );
  }
}
