const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { Langfuse } = require('langfuse');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize Langfuse
const langfuse = new Langfuse({
    secretKey: process.env.LANGFUSE_SECRET_KEY,
    publicKey: process.env.LANGFUSE_PUBLIC_KEY,
    baseUrl: process.env.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com'
});

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
        return promptCache.content;
    }

    // Try to fetch from Langfuse
    try {
        const promptName = process.env.LANGFUSE_PROMPT_NAME || 'business-partner-system';
        console.log(`[DEBUG] Attempting to fetch prompt: ${promptName}`);
        const prompt = await langfuse.getPrompt(promptName);
        console.log(`[DEBUG] Prompt fetch result:`, prompt ? 'received' : 'null/undefined');
        
        if (prompt && prompt.prompt) {
            promptCache.content = prompt.prompt;
            promptCache.fetchedAt = now;
            console.log(`✓ System prompt fetched from Langfuse: ${promptName} (v${prompt.version})`);
            return prompt.prompt;
        } else {
            console.log(`[DEBUG] Prompt object missing 'prompt' property. Full object:`, JSON.stringify(prompt));
        }
    } catch (error) {
        console.log('ℹ Using fallback prompt (Langfuse prompt not found or error):', error.message);
        console.log('[DEBUG] Full error:', error);
    }

    // Fallback to file-based prompt
    return SYSTEM_INSTRUCTIONS_FALLBACK;
}

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'ok', message: 'Business Partner API is running' });
});

// Proxy endpoint for Anthropic API with Langfuse tracing
app.post('/api/chat', async (req, res) => {
    const startTime = Date.now();
    let trace = null;
    let generation = null;

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
