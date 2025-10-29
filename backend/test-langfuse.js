const { Langfuse } = require('langfuse');
require('dotenv').config();

console.log('=== Langfuse Connection Test ===\n');

// Display configuration
console.log('Configuration:');
console.log(`  Base URL: ${process.env.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com'}`);
console.log(`  Secret Key: ${process.env.LANGFUSE_SECRET_KEY ? '✓ Set (' + process.env.LANGFUSE_SECRET_KEY.substring(0, 15) + '...)' : '✗ NOT SET'}`);
console.log(`  Public Key: ${process.env.LANGFUSE_PUBLIC_KEY ? '✓ Set (' + process.env.LANGFUSE_PUBLIC_KEY.substring(0, 15) + '...)' : '✗ NOT SET'}`);
console.log(`  Prompt Name: ${process.env.LANGFUSE_PROMPT_NAME || 'business-partner-system (default)'}`);
console.log('');

// Initialize Langfuse
const langfuse = new Langfuse({
    secretKey: process.env.LANGFUSE_SECRET_KEY,
    publicKey: process.env.LANGFUSE_PUBLIC_KEY,
    baseUrl: process.env.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com'
});

async function testConnection() {
    try {
        const promptName = process.env.LANGFUSE_PROMPT_NAME || 'business-partner-system';

        console.log(`Attempting to fetch prompt: "${promptName}"...`);

        const prompt = await langfuse.getPrompt(promptName);

        if (!prompt) {
            console.log('✗ FAILED: Prompt fetch returned null/undefined');
            console.log('\nPossible reasons:');
            console.log('  1. Prompt does not exist in Langfuse');
            console.log('  2. Prompt name is incorrect');
            console.log('  3. API credentials lack permission');
            console.log('\nNext steps:');
            console.log(`  1. Go to ${process.env.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com'}`);
            console.log('  2. Navigate to "Prompts" in the left sidebar');
            console.log(`  3. Check if a prompt named "${promptName}" exists`);
            console.log('  4. If not, create one with that exact name');
            return;
        }

        console.log('✓ SUCCESS: Prompt fetched from Langfuse!\n');
        console.log('Prompt details:');
        console.log(`  Name: ${prompt.name || 'N/A'}`);
        console.log(`  Version: ${prompt.version || 'N/A'}`);
        console.log(`  Type: ${prompt.type || 'N/A'}`);
        console.log(`  Labels: ${prompt.labels ? JSON.stringify(prompt.labels) : 'N/A'}`);
        console.log(`  Tags: ${prompt.tags ? JSON.stringify(prompt.tags) : 'N/A'}`);
        console.log('');

        // Check for the actual prompt content
        if (prompt.prompt) {
            console.log(`  Prompt Content: Available (${prompt.prompt.length} characters)`);
            console.log(`  First 100 chars: ${prompt.prompt.substring(0, 100)}...`);
        } else {
            console.log('  ✗ WARNING: Prompt object exists but missing "prompt" property');
            console.log('  Available properties:', Object.keys(prompt));
            console.log('  Full object:', JSON.stringify(prompt, null, 2));
        }

    } catch (error) {
        console.log('✗ FAILED: Error fetching prompt\n');
        console.log('Error details:');
        console.log(`  Message: ${error.message}`);
        console.log(`  Type: ${error.constructor.name}`);

        if (error.response) {
            console.log(`  HTTP Status: ${error.response.status}`);
            console.log(`  Response:`, error.response.data);
        }

        if (error.code) {
            console.log(`  Error Code: ${error.code}`);
        }

        console.log('\nFull error:');
        console.log(error);

        console.log('\nPossible solutions:');
        console.log('  1. Check that your Langfuse credentials are correct');
        console.log('  2. Verify the Base URL matches your Langfuse instance');
        console.log('  3. Ensure the prompt exists in your Langfuse project');
        console.log('  4. Check network connectivity to Langfuse');
    }
}

testConnection();
