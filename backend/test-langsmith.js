/**
 * LangSmith Connection Test Script
 *
 * This script tests your LangSmith configuration and verifies that:
 * 1. The API key is valid
 * 2. The client can connect to LangSmith
 * 3. You can create and update runs
 *
 * Usage:
 *   node test-langsmith.js
 */

require('dotenv').config();
const { Client } = require('langsmith');

async function testLangSmith() {
    console.log('=== LangSmith Connection Test ===\n');

    // Check if API key is set
    if (!process.env.LANGSMITH_API_KEY) {
        console.error('❌ LANGSMITH_API_KEY not found in environment variables');
        console.log('\nPlease set LANGSMITH_API_KEY in your .env file:');
        console.log('LANGSMITH_API_KEY=your_api_key_here');
        process.exit(1);
    }

    console.log('✅ LANGSMITH_API_KEY found');
    console.log(`   Key starts with: ${process.env.LANGSMITH_API_KEY.substring(0, 10)}...`);
    console.log(`   Project: ${process.env.LANGSMITH_PROJECT || 'business-partner-demo'}`);
    console.log(`   Endpoint: ${process.env.LANGSMITH_ENDPOINT || 'https://api.smith.langchain.com'}\n`);

    try {
        // Initialize client
        console.log('Initializing LangSmith client...');
        const client = new Client({
            apiKey: process.env.LANGSMITH_API_KEY,
            apiUrl: process.env.LANGSMITH_ENDPOINT
        });
        console.log('✅ Client initialized\n');

        // Test creating a run
        console.log('Creating test run...');
        const runId = await client.createRun({
            name: 'langsmith-connection-test',
            run_type: 'chain',
            inputs: {
                test: 'This is a test message',
                timestamp: new Date().toISOString()
            },
            project_name: process.env.LANGSMITH_PROJECT || 'business-partner-demo',
            tags: ['test', 'connection-test']
        });
        console.log(`✅ Run created successfully`);
        console.log(`   Run ID: ${runId}\n`);

        // Test updating the run
        console.log('Updating test run...');
        await client.updateRun(runId, {
            outputs: {
                result: 'Connection test successful!',
                status: 'completed'
            },
            end_time: new Date().toISOString()
        });
        console.log('✅ Run updated successfully\n');

        // Success message
        console.log('🎉 LangSmith integration is working correctly!');
        console.log('\nNext steps:');
        console.log('1. Start your server: npm start');
        console.log('2. Send a chat message');
        console.log('3. Check your LangSmith dashboard at https://smith.langchain.com');
        console.log(`4. Look for runs in the "${process.env.LANGSMITH_PROJECT || 'business-partner-demo'}" project\n`);

    } catch (error) {
        console.error('\n❌ LangSmith test failed');
        console.error(`Error: ${error.message}\n`);

        if (error.message.includes('401') || error.message.includes('unauthorized')) {
            console.log('💡 This looks like an authentication error.');
            console.log('   Check that your LANGSMITH_API_KEY is correct.');
        } else if (error.message.includes('404') || error.message.includes('not found')) {
            console.log('💡 This might be a project or endpoint issue.');
            console.log('   Check that your LANGSMITH_PROJECT exists in the dashboard.');
        } else if (error.message.includes('ENOTFOUND') || error.message.includes('ECONNREFUSED')) {
            console.log('💡 This looks like a network connectivity issue.');
            console.log('   Check your internet connection and firewall settings.');
        }

        console.log('\nFull error details:');
        console.error(error);
        process.exit(1);
    }
}

// Run the test
testLangSmith();
