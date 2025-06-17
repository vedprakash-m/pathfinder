#!/usr/bin/env node

const { MongoClient } = require('mongodb');

const MONGODB_URL = process.env.MONGODB_URL || 'mongodb://localhost:27018/pathfinder_e2e';

const TEST_USERS = [
  {
    email: 'user1@e2e.test',
    name: 'Test User One',
    auth0_id: 'auth0|e2e_user_1',
    is_active: true,
    created_at: new Date(),
    updated_at: new Date(),
  },
  {
    email: 'user2@e2e.test',
    name: 'Test User Two',
    auth0_id: 'auth0|e2e_user_2',
    is_active: true,
    created_at: new Date(),
    updated_at: new Date(),
  },
  {
    email: 'admin@family.test',
    name: 'Family Admin',
    auth0_id: 'auth0|family_admin',
    is_active: true,
    created_at: new Date(),
    updated_at: new Date(),
  },
];

const TEST_FAMILY = {
  name: 'E2E Test Family',
  description: 'A test family for E2E testing',
  preferences: {
    activities: ['sightseeing', 'restaurants', 'museums'],
    budget_level: 'medium',
    dietary_restrictions: ['vegetarian'],
    accessibility_needs: [],
    travel_style: 'relaxed',
  },
  created_by: 'auth0|family_admin',
  created_at: new Date(),
  updated_at: new Date(),
};

async function setupTestData() {
  console.log('🗄️ Setting up E2E test data...');
  
  const client = new MongoClient(MONGODB_URL);
  
  try {
    await client.connect();
    const db = client.db();

    // Clear existing test data
    console.log('🧹 Clearing existing test data...');
    await db.collection('users').deleteMany({ email: { $regex: '@e2e.test$|@family.test$' } });
    await db.collection('families').deleteMany({ name: /E2E Test/ });
    await db.collection('trips').deleteMany({ title: /E2E Test/ });
    await db.collection('invitations').deleteMany({ email: { $regex: '@e2e.test$|@family.test$' } });

    // Create test users
    console.log('👥 Creating test users...');
    const userResult = await db.collection('users').insertMany(TEST_USERS);
    console.log(`✅ Created ${userResult.insertedCount} test users`);

    // Create test family
    console.log('👨‍👩‍👧‍👦 Creating test family...');
    const familyResult = await db.collection('families').insertOne(TEST_FAMILY);
    console.log(`✅ Created test family with ID: ${familyResult.insertedId}`);

    // Create family members associations
    console.log('🔗 Creating family member associations...');
    const familyMembers = TEST_USERS.map(user => ({
      family_id: familyResult.insertedId,
      user_id: user.auth0_id,
      role: user.auth0_id === 'auth0|family_admin' ? 'admin' : 'member',
      joined_at: new Date(),
      created_at: new Date(),
    }));
    
    const membersResult = await db.collection('family_members').insertMany(familyMembers);
    console.log(`✅ Created ${membersResult.insertedCount} family member associations`);

    // Create sample trip
    console.log('🧳 Creating sample trip...');
    const sampleTrip = {
      title: 'E2E Sample Trip',
      description: 'A sample trip for testing purposes',
      destination: 'San Francisco, CA',
      start_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days from now
      end_date: new Date(Date.now() + 37 * 24 * 60 * 60 * 1000), // 37 days from now
      budget_total: 3000.0,
      max_participants: 10,
      is_public: false,
      status: 'planning',
      creator_id: 'auth0|family_admin',
      family_id: familyResult.insertedId,
      created_at: new Date(),
      updated_at: new Date(),
    };
    
    const tripResult = await db.collection('trips').insertOne(sampleTrip);
    console.log(`✅ Created sample trip with ID: ${tripResult.insertedId}`);

    console.log('\n🎯 E2E test data setup complete!');
    console.log(`📧 Test user emails: ${TEST_USERS.map(u => u.email).join(', ')}`);
    console.log(`👨‍👩‍👧‍👦 Test family: ${TEST_FAMILY.name}`);
    console.log(`🧳 Sample trip: ${sampleTrip.title}`);

  } catch (error) {
    console.error('❌ Failed to setup test data:', error);
    process.exit(1);
  } finally {
    await client.close();
  }
}

if (require.main === module) {
  setupTestData().catch(console.error);
}

module.exports = { setupTestData };
