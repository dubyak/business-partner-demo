const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { Langfuse } = require('langfuse');
const { Client } = require('langsmith');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize Langfuse
console.log('[LANGFUSE] Initializing with config:');
console.log(`  - Base URL: ${process.env.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com'}`);
console.log(`  - Secret Key: ${process.env.LANGFUSE_SECRET_KEY ? 'Set (starts with ' + process.env.LANGFUSE_SECRET_KEY.substring(0, 10) + '...)' : 'NOT SET'}`);
console.log(`  - Public Key: ${process.env.LANGFUSE_PUBLIC_KEY ? 'Set (starts with ' + process.env.LANGFUSE_PUBLIC_KEY.substring(0, 10) + '...)' : 'NOT SET'}`);

const langfuse = new Langfuse({
    secretKey: process.env.LANGFUSE_SECRET_KEY,
    publicKey: process.env.LANGFUSE_PUBLIC_KEY,
    baseUrl: process.env.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com'
});

// Initialize LangSmith
let langsmithClient = null;
if (process.env.LANGSMITH_API_KEY) {
    console.log('[LANGSMITH] Initializing with config:');
    console.log(`  - API Key: Set (starts with ${process.env.LANGSMITH_API_KEY.substring(0, 10)}...)`);
    console.log(`  - Project: ${process.env.LANGSMITH_PROJECT || 'business-partner-demo'}`);
    console.log(`  - Endpoint: ${process.env.LANGSMITH_ENDPOINT || 'https://api.smith.langchain.com'}`);

    langsmithClient = new Client({
        apiKey: process.env.LANGSMITH_API_KEY,
        apiUrl: process.env.LANGSMITH_ENDPOINT
    });
} else {
    console.log('[LANGSMITH] Not initialized - LANGSMITH_API_KEY not set');
}

// Load system instructions from file (fallback)
const systemInstructionsPath = path.join(__dirname, '..', 'system-instructions.md');
let SYSTEM_INSTRUCTIONS_FALLBACK = '';
try {
    SYSTEM_INSTRUCTIONS_FALLBACK = fs.readFileSync(systemInstructionsPath, 'utf8');
    console.log('✓ System instructions fallback loaded from file');
} catch (error) {
    console.error('Warning: Could not load system-instructions.md:', error.message);
    SYSTEM_INSTRUCTIONS_FALLBACK = 'You are a helpful business partner assistant.';
}

// Cache for Langfuse prompt
let promptCache = {
    content: null,
    fetchedAt: null,
    ttl: 60000 // Cache for 1 minute
};

// Function to get system prompt from Langfuse or fallback
async function getSystemPrompt() {
    const now = Date.now();

    // Return cached prompt if still valid
    if (promptCache.content && promptCache.fetchedAt && (now - promptCache.fetchedAt < promptCache.ttl)) {
        const cacheAge = Math.floor((now - promptCache.fetchedAt) / 1000);
        console.log(`[LANGFUSE] Using cached prompt (age: ${cacheAge}s / ${promptCache.ttl / 1000}s TTL)`);
        return promptCache.content;
    }

    // Try to fetch from Langfuse
    try {
        const promptName = process.env.LANGFUSE_PROMPT_NAME || 'business-partner-system';
        console.log(`[LANGFUSE] Attempting to fetch prompt: "${promptName}"`);
        console.log(`[LANGFUSE] Connecting to: ${process.env.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com'}`);

        const prompt = await langfuse.getPrompt(promptName);
        console.log(`[LANGFUSE] Prompt fetch result:`, prompt ? 'received' : 'null/undefined');

        if (prompt && prompt.prompt) {
            promptCache.content = prompt.prompt;
            promptCache.fetchedAt = now;
            console.log(`[LANGFUSE] ✓ System prompt fetched successfully: ${promptName} (v${prompt.version})`);
            console.log(`[LANGFUSE] Prompt length: ${prompt.prompt.length} characters`);
            return prompt.prompt;
        } else if (prompt) {
            console.log(`[LANGFUSE] ✗ Prompt object missing 'prompt' property`);
            console.log(`[LANGFUSE] Received object keys:`, Object.keys(prompt));
            console.log(`[LANGFUSE] Full object:`, JSON.stringify(prompt, null, 2));
        } else {
            console.log(`[LANGFUSE] ✗ Prompt fetch returned null/undefined`);
        }
    } catch (error) {
        console.log(`[LANGFUSE] ✗ Error fetching prompt: ${error.message}`);
        console.log(`[LANGFUSE] Error type: ${error.constructor.name}`);
        if (error.response) {
            console.log(`[LANGFUSE] Response status: ${error.response.status}`);
            console.log(`[LANGFUSE] Response data:`, error.response.data);
        }
        console.log('[LANGFUSE] Full error stack:', error.stack);
    }

    // Fallback to file-based prompt
    console.log(`[LANGFUSE] → Falling back to file-based system instructions (${SYSTEM_INSTRUCTIONS_FALLBACK.length} chars)`);
    return SYSTEM_INSTRUCTIONS_FALLBACK;
}

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'ok', message: 'Business Partner API is running' });
});

// Proxy endpoint for Anthropic API with Langfuse and LangSmith tracing
app.post('/api/chat', async (req, res) => {
    const startTime = Date.now();
    let trace = null;
    let generation = null;
    let langsmithRunId = null;

    try {
        const { model, max_tokens, system, messages, sessionId, userId } = req.body;

        // Validate request
        if (!messages || !Array.isArray(messages)) {
            return res.status(400).json({ error: 'Invalid request: messages array required' });
        }

        // Check for API key
        const apiKey = process.env.ANTHROPIC_API_KEY;
        if (!apiKey) {
            return res.status(500).json({ error: 'Server configuration error: API key not set' });
        }

        // Get system prompt from Langfuse or fallback (allow override for testing)
        const systemPrompt = system || await getSystemPrompt();

        // Create Langfuse trace for this conversation
        trace = langfuse.trace({
            name: 'business-partner-chat',
            sessionId: sessionId || `session-${Date.now()}`,
            userId: userId || 'demo-user',
            input: messages, // Add input at trace level
            metadata: {
                model: model || 'claude-sonnet-4-20250514',
                timestamp: new Date().toISOString()
            }
        });

        // Log the generation
        generation = trace.generation({
            name: 'anthropic-api-call',
            model: model || 'claude-sonnet-4-20250514',
            modelParameters: {
                maxTokens: max_tokens || 1024
            },
            input: messages,
            metadata: {
                systemPromptLength: systemPrompt.length,
                messageCount: messages.length,
                promptSource: promptCache.content ? 'langfuse' : 'file'
            }
        });

        // Create LangSmith trace if enabled
        if (langsmithClient) {
            try {
                const runId = await langsmithClient.createRun({
                    name: 'business-partner-chat',
                    run_type: 'chain',
                    inputs: {
                        messages: messages,
                        systemPrompt: systemPrompt.substring(0, 500) + '...' // Truncate for readability
                    },
                    project_name: process.env.LANGSMITH_PROJECT || 'business-partner-demo',
                    tags: ['anthropic', 'claude', 'business-partner'],
                    extra: {
                        metadata: {
                            model: model || 'claude-sonnet-4-20250514',
                            max_tokens: max_tokens || 1024,
                            sessionId: sessionId || `session-${Date.now()}`,
                            userId: userId || 'demo-user',
                            systemPromptLength: systemPrompt.length,
                            messageCount: messages.length
                        }
                    }
                });
                langsmithRunId = runId;
                console.log(`[LANGSMITH] Created run: ${runId}`);
            } catch (error) {
                console.error('[LANGSMITH] Error creating run:', error.message);
            }
        }

        // Call Anthropic API
        const response = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': apiKey,
                'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify({
                model: model || 'claude-sonnet-4-20250514',
                max_tokens: max_tokens || 1024,
                system: systemPrompt,
                messages: messages
            })
        });

        if (!response.ok) {
            const errorData = await response.text();
            console.error('Anthropic API error:', response.status, errorData);
            
            // Log error to Langfuse
            if (generation) {
                generation.end({
                    level: 'ERROR',
                    statusMessage: `API error: ${response.status}`
                });
            }
            
            return res.status(response.status).json({ 
                error: 'API request failed', 
                details: errorData 
            });
        }

        const data = await response.json();
        const endTime = Date.now();

        // Log successful response to Langfuse
        if (generation) {
            generation.end({
                output: data.content,
                usage: {
                    input: data.usage?.input_tokens || 0,
                    output: data.usage?.output_tokens || 0,
                    total: (data.usage?.input_tokens || 0) + (data.usage?.output_tokens || 0)
                },
                metadata: {
                    latencyMs: endTime - startTime,
                    stopReason: data.stop_reason
                }
            });
        }

        // Update trace with output
        if (trace) {
            trace.update({
                output: data.content
            });
        }

        // Update LangSmith run if enabled
        if (langsmithClient && langsmithRunId) {
            try {
                await langsmithClient.updateRun(langsmithRunId, {
                    outputs: {
                        content: data.content,
                        stop_reason: data.stop_reason
                    },
                    end_time: new Date().toISOString(),
                    extra: {
                        usage: {
                            input_tokens: data.usage?.input_tokens || 0,
                            output_tokens: data.usage?.output_tokens || 0,
                            total_tokens: (data.usage?.input_tokens || 0) + (data.usage?.output_tokens || 0)
                        },
                        latency_ms: endTime - startTime
                    }
                });
                console.log(`[LANGSMITH] Updated run: ${langsmithRunId}`);
            } catch (error) {
                console.error('[LANGSMITH] Error updating run:', error.message);
            }
        }

        // Finalize trace
        await langfuse.flushAsync();

        res.json(data);

    } catch (error) {
        console.error('Error in /api/chat:', error);

        // Log error to Langfuse
        if (generation) {
            generation.end({
                level: 'ERROR',
                statusMessage: error.message
            });
        }

        // Log error to LangSmith
        if (langsmithClient && langsmithRunId) {
            try {
                await langsmithClient.updateRun(langsmithRunId, {
                    error: error.message,
                    end_time: new Date().toISOString(),
                    outputs: {
                        error: error.message,
                        stack: error.stack
                    }
                });
                console.log(`[LANGSMITH] Updated run with error: ${langsmithRunId}`);
            } catch (updateError) {
                console.error('[LANGSMITH] Error updating run with error:', updateError.message);
            }
        }

        res.status(500).json({
            error: 'Internal server error',
            message: error.message
        });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Health check: http://localhost:${PORT}/health`);
});
