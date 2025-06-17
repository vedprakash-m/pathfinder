// MongoDB initialization script for E2E testing
// This script runs when the MongoDB container starts

print('🗄️ Initializing Pathfinder E2E Test Database...');

// Switch to the test database
db = db.getSiblingDB('pathfinder_e2e');

// Create collections with proper schemas
print('📋 Creating collections...');

// Users collection
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['email', 'auth0_id', 'name'],
      properties: {
        email: { bsonType: 'string' },
        auth0_id: { bsonType: 'string' },
        name: { bsonType: 'string' },
        is_active: { bsonType: 'bool' },
        created_at: { bsonType: 'date' },
        updated_at: { bsonType: 'date' }
      }
    }
  }
});

// Families collection
db.createCollection('families', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'created_by'],
      properties: {
        name: { bsonType: 'string' },
        description: { bsonType: 'string' },
        created_by: { bsonType: 'string' },
        preferences: { bsonType: 'object' },
        created_at: { bsonType: 'date' },
        updated_at: { bsonType: 'date' }
      }
    }
  }
});

// Trips collection
db.createCollection('trips', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['title', 'creator_id'],
      properties: {
        title: { bsonType: 'string' },
        description: { bsonType: 'string' },
        destination: { bsonType: 'string' },
        creator_id: { bsonType: 'string' },
        family_id: { bsonType: 'objectId' },
        start_date: { bsonType: 'date' },
        end_date: { bsonType: 'date' },
        budget_total: { bsonType: 'number' },
        status: { 
          bsonType: 'string',
          enum: ['planning', 'confirmed', 'active', 'completed', 'cancelled']
        },
        is_public: { bsonType: 'bool' },
        created_at: { bsonType: 'date' },
        updated_at: { bsonType: 'date' }
      }
    }
  }
});

// Create indexes for better performance
print('📌 Creating indexes...');

// Users indexes
db.users.createIndex({ 'email': 1 }, { unique: true });
db.users.createIndex({ 'auth0_id': 1 }, { unique: true });
db.users.createIndex({ 'email': 1, 'auth0_id': 1 });

// Families indexes
db.families.createIndex({ 'name': 1 });
db.families.createIndex({ 'created_by': 1 });
db.families.createIndex({ 'created_at': -1 });

// Trips indexes
db.trips.createIndex({ 'title': 1 });
db.trips.createIndex({ 'creator_id': 1 });
db.trips.createIndex({ 'family_id': 1 });
db.trips.createIndex({ 'status': 1 });
db.trips.createIndex({ 'start_date': 1 });
db.trips.createIndex({ 'created_at': -1 });

// Family members indexes
db.family_members.createIndex({ 'family_id': 1 });
db.family_members.createIndex({ 'user_id': 1 });
db.family_members.createIndex({ 'family_id': 1, 'user_id': 1 }, { unique: true });

// Invitations indexes
db.invitations.createIndex({ 'email': 1 });
db.invitations.createIndex({ 'family_id': 1 });
db.invitations.createIndex({ 'status': 1 });
db.invitations.createIndex({ 'expires_at': 1 });

print('✅ E2E test database initialization complete!');
print('📊 Collections created:', db.getCollectionNames());
print('🔍 Database stats:');
printjson(db.stats());
