#!/usr/bin/env node

const { MongoClient } = require('mongodb');

const MONGODB_URL = process.env.MONGODB_URL || 'mongodb://localhost:27018/pathfinder_e2e';

async function cleanupTestData() {
  console.log('🧹 Cleaning up E2E test data...');
  
  const client = new MongoClient(MONGODB_URL);
  
  try {
    await client.connect();
    const db = client.db();

    // Clean up test data
    const cleanupOps = [
      db.collection('users').deleteMany({ email: { $regex: '@e2e.test$|@family.test$' } }),
      db.collection('families').deleteMany({ name: /E2E Test/ }),
      db.collection('family_members').deleteMany({ user_id: { $regex: 'auth0\\|e2e_|auth0\\|family_admin' } }),
      db.collection('trips').deleteMany({ title: /E2E Test|E2E Sample/ }),
      db.collection('invitations').deleteMany({ email: { $regex: '@e2e.test$|@family.test$' } }),
      db.collection('itineraries').deleteMany({ trip_id: { $in: [] } }), // Clean orphaned itineraries
      db.collection('messages').deleteMany({ sender: { $regex: 'auth0\\|e2e_|auth0\\|family_admin' } }),
    ];

    const results = await Promise.all(cleanupOps);
    
    console.log('🗑️ Cleanup Results:');
    console.log(`   Users: ${results[0].deletedCount} deleted`);
    console.log(`   Families: ${results[1].deletedCount} deleted`);
    console.log(`   Family Members: ${results[2].deletedCount} deleted`);
    console.log(`   Trips: ${results[3].deletedCount} deleted`);
    console.log(`   Invitations: ${results[4].deletedCount} deleted`);
    console.log(`   Itineraries: ${results[5].deletedCount} deleted`);
    console.log(`   Messages: ${results[6].deletedCount} deleted`);

    const totalDeleted = results.reduce((sum, result) => sum + result.deletedCount, 0);
    console.log(`\n✅ E2E test data cleanup complete! (${totalDeleted} documents removed)`);

  } catch (error) {
    console.error('❌ Failed to cleanup test data:', error);
    process.exit(1);
  } finally {
    await client.close();
  }
}

if (require.main === module) {
  cleanupTestData().catch(console.error);
}

module.exports = { cleanupTestData };
