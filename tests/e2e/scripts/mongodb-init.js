#!/usr/bin/env node

const { MongoClient } = require('mongodb');

const MONGODB_URL = process.env.MONGODB_URL || 'mongodb://localhost:27018/pathfinder_e2e';

async function initializeMongoDB() {
  console.log('🗄️ Initializing MongoDB for E2E testing...');
  
  const client = new MongoClient(MONGODB_URL);
  
  try {
    await client.connect();
    const db = client.db();

    console.log('📋 Creating collections and indexes...');

    // Create collections with indexes
    const collections = [
      {
        name: 'users',
        indexes: [
          { email: 1 },
          { auth0_id: 1 },
          { 'email': 1, 'auth0_id': 1 }
        ]
      },
      {
        name: 'families',
        indexes: [
          { name: 1 },
          { created_by: 1 },
          { created_at: -1 }
        ]
      },
      {
        name: 'family_members',
        indexes: [
          { family_id: 1 },
          { user_id: 1 },
          { family_id: 1, user_id: 1 }
        ]
      },
      {
        name: 'trips',
        indexes: [
          { title: 1 },
          { creator_id: 1 },
          { family_id: 1 },
          { status: 1 },
          { start_date: 1 },
          { created_at: -1 }
        ]
      },
      {
        name: 'invitations',
        indexes: [
          { email: 1 },
          { family_id: 1 },
          { status: 1 },
          { expires_at: 1 }
        ]
      },
      {
        name: 'itineraries',
        indexes: [
          { trip_id: 1 },
          { created_at: -1 }
        ]
      },
      {
        name: 'messages',
        indexes: [
          { trip_id: 1 },
          { sender: 1 },
          { created_at: -1 }
        ]
      }
    ];

    for (const collection of collections) {
      // Create collection if it doesn't exist
      const existingCollections = await db.listCollections({ name: collection.name }).toArray();
      if (existingCollections.length === 0) {
        await db.createCollection(collection.name);
        console.log(`✅ Created collection: ${collection.name}`);
      }

      // Create indexes
      for (const index of collection.indexes) {
        try {
          await db.collection(collection.name).createIndex(index);
          console.log(`   📌 Index created on ${collection.name}: ${JSON.stringify(index)}`);
        } catch (error) {
          if (error.code === 85) {
            // Index already exists
            console.log(`   ⚡ Index already exists on ${collection.name}: ${JSON.stringify(index)}`);
          } else {
            console.warn(`   ⚠️ Failed to create index on ${collection.name}: ${error.message}`);
          }
        }
      }
    }

    // Initialize replica set if needed (for transactions)
    try {
      const status = await db.admin().command({ replSetGetStatus: 1 });
      console.log('✅ Replica set already initialized');
    } catch (error) {
      if (error.code === 94) {
        console.log('🔧 Initializing replica set...');
        try {
          await db.admin().command({
            replSetInitiate: {
              _id: 'rs0',
              members: [{ _id: 0, host: 'localhost:27017' }]
            }
          });
          console.log('✅ Replica set initialized');
          
          // Wait for replica set to be ready
          await new Promise(resolve => setTimeout(resolve, 5000));
        } catch (initError) {
          console.warn('⚠️ Could not initialize replica set:', initError.message);
        }
      }
    }

    console.log('\n🎯 MongoDB initialization complete!');

  } catch (error) {
    console.error('❌ Failed to initialize MongoDB:', error);
    process.exit(1);
  } finally {
    await client.close();
  }
}

if (require.main === module) {
  initializeMongoDB().catch(console.error);
}

module.exports = { initializeMongoDB };
