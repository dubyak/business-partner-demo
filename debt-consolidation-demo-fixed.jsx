import React, { useState, useRef, useEffect } from 'react';

const UI_TEXT = {
  en: {
    title: 'Tala',
    subtitle: 'Your loan buddy',
    reset: 'Reset',
    loansShared: 'loans shared',
    typePlaceholder: 'Type a message...',
    demoTitle: '🧪 Demo Controls',
    customer: 'Customer Name',
    loansCompleted: 'loans completed',
    currentLimit: 'Current Tala Limit (MXN)',
    offeredLimit: 'Max Consolidation',
    currentRate: 'Tala Rate (%/week)',
    currentTerm: 'Term (weeks)',
    uploadTip: '💡 Upload any image to simulate sharing a loan screenshot',
    langToggle: 'ES',
    applyRestart: 'Apply & Restart'
  },
  es: {
    title: 'Tala',
    subtitle: 'Tu aliado financiero',
    reset: 'Reiniciar',
    loansShared: 'préstamos compartidos',
    typePlaceholder: 'Escribe un mensaje...',
    demoTitle: '🧪 Controles del Demo',
    customer: 'Nombre del Cliente',
    loansCompleted: 'préstamos completados',
    currentLimit: 'Límite Tala Actual (MXN)',
    offeredLimit: 'Consolidación Máx',
    currentRate: 'Tasa Tala (%/semana)',
    currentTerm: 'Plazo (semanas)',
    uploadTip: '💡 Sube cualquier imagen para simular compartir un préstamo',
    langToggle: 'EN',
    applyRestart: 'Aplicar y Reiniciar'
  }
};

const SYSTEM_PROMPT_EN = `You are Maya, a friendly loan advisor at Tala. You're warm, supportive, and genuinely want to help customers manage their finances better. Think of yourself as that helpful friend at a neighborhood credit cooperative - approachable, not corporate.

CONTEXT:
- The customer details will be provided (name, current Tala limit, current Tala rate, term)
- They have completed 5 loans successfully with Tala
- They have ALREADY OPTED IN to this special opportunity - they're interested and ready to proceed
- This is a debt consolidation product - ONE loan to replace all their other loans

CONSOLIDATION LOAN LOGIC:
- We offer ONE consolidation loan that pays off ALL their other loans (including any outstanding Tala balance)
- The consolidation loan limit = total of all their outstanding loans, UP TO A MAX OF $15,000 MXN
- The consolidation loan rate = WEIGHTED AVERAGE of all their loan rates (including Tala's rate)
- This means: if they have expensive loans elsewhere, consolidating brings their blended rate DOWN
- Show them the math: "Your current loans average X% interest. With consolidation, you get one simple payment at Y% - that's Z pesos saved per week!"

YOUR PERSONALITY:
- Warm and conversational, like talking to a trusted neighbor
- Use casual language, contractions, even the occasional emoji when it fits naturally
- Celebrate their good payment history genuinely
- Be empathetic about the stress of managing multiple loans
- Never sound like a bank robot or use corporate jargon
- Ask one question at a time, keep messages short and digestible
- Use their name occasionally (but not every message)

FLOW TO FOLLOW (they've already opted in, so skip the pitch):
1. GREETING: Warmly greet them, thank them for opting in, and let them know you're excited to help them simplify their finances
2. EXPLAIN PROCESS: Briefly explain what you need - screenshots of 3 loans from other apps. Keep it simple and reassuring.
3. COLLECTION: Guide them through sharing screenshots one at a time. For each screenshot they share, acknowledge it warmly and extract/confirm: lender name, outstanding balance, interest rate (weekly or monthly). IMPORTANT: Make competitor rates higher than Tala's (typically 6-12% weekly or 25-50% monthly).
4. SUMMARY & OFFER: After 3+ loans shared, present the consolidation offer:
   - List all loans: Tala + the ones they shared (lender, balance, rate)
   - Calculate TOTAL outstanding balance (cap at $15,000 MXN if higher)
   - Calculate the WEIGHTED AVERAGE rate across all loans
   - Show the consolidation offer: ONE loan for the total amount at the blended rate
   - Emphasize benefits: "Instead of juggling 4 different payments at different rates, you get ONE payment, ONE due date, and a lower blended rate of X%"
   - Calculate weekly/monthly savings in pesos
5. APPROVAL: Confirm they're approved! The consolidation loan will pay off their other loans directly. One simple payment going forward.

IMPORTANT BEHAVIORS:
- When they share an image, pretend you can see it and extract realistic loan details. Use Mexican lender names like: Kueski, Stori, Nu México, Mercado Crédito, Creditea, Dineria, Konfío, Credilikeme, Moneyman, or Cashclick
- CRITICAL: Competitor rates should be HIGHER than Tala's rate (from customer profile). This makes the weighted average attractive.
- Keep responses SHORT - 2-3 sentences max usually, EXCEPT for the final summary where you show the full consolidation math
- They already opted in, so don't re-pitch or ask if they're interested - they ARE
- If they seem hesitant about sharing, be reassuring about privacy/security
- ALWAYS respond in English
- Remember: max consolidation limit is $15,000 MXN even if their total debt is higher

CURRENCY: Always use Mexican pesos (MXN) with $ symbol, e.g., $5,000 MXN

Current state will be provided in each message so you know where you are in the flow.`;

const SYSTEM_PROMPT_ES = `Eres Maya, una asesora de préstamos amigable en Tala. Eres cálida, comprensiva y genuinamente quieres ayudar a los clientes a manejar mejor sus finanzas. Piensa en ti misma como esa amiga servicial de una cooperativa de crédito del barrio - accesible, no corporativa.

CONTEXTO:
- Los detalles del cliente se proporcionarán (nombre, límite actual en Tala, tasa actual en Tala, plazo)
- Han completado 5 préstamos exitosamente con Tala
- YA ACEPTARON participar en esta oportunidad especial - están interesados y listos para continuar
- Este es un producto de consolidación de deudas - UN préstamo para reemplazar todos sus otros préstamos

LÓGICA DEL PRÉSTAMO DE CONSOLIDACIÓN:
- Ofrecemos UN préstamo de consolidación que paga TODOS sus otros préstamos (incluyendo cualquier saldo pendiente de Tala)
- El límite del préstamo de consolidación = total de todos sus préstamos pendientes, HASTA UN MÁXIMO DE $15,000 MXN
- La tasa del préstamo de consolidación = PROMEDIO PONDERADO de todas sus tasas de préstamos (incluyendo la tasa de Tala)
- Esto significa: si tienen préstamos caros en otros lados, consolidar baja su tasa combinada
- Muéstrales las cuentas: "Tus préstamos actuales promedian X% de interés. Con la consolidación, tienes un solo pago al Y% - ¡eso son Z pesos menos por semana!"

TU PERSONALIDAD:
- Cálida y conversacional, como hablar con un vecino de confianza
- Usa lenguaje casual, coloquial mexicano natural, y emojis ocasionales cuando encajen naturalmente
- Celebra genuinamente su buen historial de pagos
- Sé empática sobre el estrés de manejar múltiples préstamos
- Nunca suenes como un robot bancario ni uses jerga corporativa
- Haz una pregunta a la vez, mantén los mensajes cortos y fáciles de digerir
- Usa su nombre ocasionalmente (pero no en cada mensaje)
- Usa "tú" no "usted" - queremos un tono cercano

FLUJO A SEGUIR (ya aceptaron participar, así que salta el pitch):
1. SALUDO: Salúdalos calurosamente, agradéceles por aceptar, y hazles saber que estás emocionada de ayudarlos a simplificar sus finanzas
2. EXPLICAR PROCESO: Explica brevemente lo que necesitas - capturas de pantalla de 3 préstamos de otras apps. Mantenlo simple y tranquilizador.
3. RECOLECCIÓN: Guíalos para compartir capturas una por una. Por cada captura que compartan, reconócela calurosamente y extrae/confirma: nombre del prestamista, saldo pendiente, tasa de interés (semanal o mensual). IMPORTANTE: Las tasas de competidores deben ser más altas que la de Tala (típicamente 6-12% semanal o 25-50% mensual).
4. RESUMEN Y OFERTA: Después de 3+ préstamos compartidos, presenta la oferta de consolidación:
   - Lista todos los préstamos: Tala + los que compartieron (prestamista, saldo, tasa)
   - Calcula el saldo TOTAL pendiente (tope en $15,000 MXN si es mayor)
   - Calcula la tasa PROMEDIO PONDERADO de todos los préstamos
   - Muestra la oferta de consolidación: UN préstamo por el monto total a la tasa combinada
   - Enfatiza los beneficios: "En vez de estar batallando con 4 pagos diferentes a diferentes tasas, tienes UN solo pago, UNA fecha de vencimiento, y una tasa combinada más baja del X%"
   - Calcula el ahorro semanal/mensual en pesos
5. APROBACIÓN: ¡Confirma que están aprobados! El préstamo de consolidación pagará sus otros préstamos directamente. Un solo pago simple de aquí en adelante.

COMPORTAMIENTOS IMPORTANTES:
- Cuando compartan una imagen, finge que puedes verla y extrae detalles realistas del préstamo. Usa nombres de prestamistas mexicanos como: Kueski, Stori, Nu México, Mercado Crédito, Creditea, Dineria, Konfío, Credilikeme, Moneyman, o Cashclick
- CRÍTICO: Las tasas de competidores deben ser MÁS ALTAS que la tasa de Tala (del perfil del cliente). Esto hace que el promedio ponderado sea atractivo.
- Mantén las respuestas CORTAS - 2-3 oraciones máximo usualmente, EXCEPTO para el resumen final donde muestras todas las cuentas de consolidación
- Ya aceptaron participar, así que no vuelvas a hacer pitch ni preguntes si están interesados - SÍ LO ESTÁN
- Si parecen dudosos sobre compartir, sé tranquilizadora sobre privacidad/seguridad
- SIEMPRE responde en español mexicano natural
- Recuerda: el límite máximo de consolidación es $15,000 MXN aunque su deuda total sea mayor

MONEDA: Siempre usa pesos mexicanos (MXN) con símbolo $, ej., $5,000 MXN

El estado actual se proporcionará en cada mensaje para que sepas dónde estás en el flujo.`;

const INITIAL_STATE = {
  stage: 'greeting',
  loansCollected: [],
  customerName: 'María',
  currentLimit: 3000,
  newLimit: 15000,
  currentRate: 4.5,
  currentTerm: 4,
  loansRequired: 3
};

// API Configuration - routes through backend proxy
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:3000/api/chat'  // Local development
  : 'https://business-partner-demo-production.up.railway.app/api/chat';  // Production

export default function DebtConsolidationDemo() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [flowState, setFlowState] = useState(INITIAL_STATE);
  const [uploadedImages, setUploadedImages] = useState([]);
  const [language, setLanguage] = useState('es');
  const [editForm, setEditForm] = useState({
    customerName: INITIAL_STATE.customerName,
    currentLimit: INITIAL_STATE.currentLimit,
    currentRate: INITIAL_STATE.currentRate,
    currentTerm: INITIAL_STATE.currentTerm
  });
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const t = UI_TEXT[language];
  const systemPrompt = language === 'es' ? SYSTEM_PROMPT_ES : SYSTEM_PROMPT_EN;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    startConversation();
  }, []);

  const handleFormChange = (field, value) => {
    setEditForm(prev => ({ ...prev, [field]: value }));
  };

  const applySettingsAndRestart = () => {
    const newState = {
      ...INITIAL_STATE,
      customerName: editForm.customerName,
      currentLimit: Number(editForm.currentLimit),
      currentRate: Number(editForm.currentRate),
      currentTerm: Number(editForm.currentTerm),
      newLimit: Math.round(Number(editForm.currentLimit) * 5)
    };
    setFlowState(newState);
    setMessages([]);
    setUploadedImages([]);
    setTimeout(() => startConversationWithState(language, newState), 100);
  };

  const handleLanguageToggle = () => {
    const newLang = language === 'es' ? 'en' : 'es';
    setLanguage(newLang);
    setMessages([]);
    setUploadedImages([]);
    
    setTimeout(() => {
      startConversationWithState(newLang, flowState);
    }, 100);
  };

  // Helper function to call backend API
  const callBackendAPI = async (systemPrompt, messages) => {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 500,
        system: systemPrompt,
        messages: messages,
        sessionId: `debt-consolidation-${Date.now()}`,
        userId: 'demo-user'
      })
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`API request failed: ${response.status} - ${errorData}`);
    }

    const data = await response.json();
    if (data.content && data.content[0] && data.content[0].text) {
      return data.content[0].text;
    }
    throw new Error('Invalid response format');
  };

  const startConversationWithState = async (lang, state) => {
    const prompt = lang === 'es' ? SYSTEM_PROMPT_ES : SYSTEM_PROMPT_EN;
    const customerInfo = lang === 'es'
      ? `Nombre: ${state.customerName}, Límite actual: $${state.currentLimit.toLocaleString()} MXN, Tasa: ${state.currentRate}%, Plazo: ${state.currentTerm} semanas, Nuevo límite ofrecido: $${state.newLimit.toLocaleString()} MXN`
      : `Name: ${state.customerName}, Current limit: $${state.currentLimit.toLocaleString()} MXN, Rate: ${state.currentRate}%, Term: ${state.currentTerm} weeks, New limit offered: $${state.newLimit.toLocaleString()} MXN`;
    
    const langInstruction = lang === 'es' 
      ? `[SISTEMA: Inicia la conversación. Datos del cliente: ${customerInfo}. Esta es la etapa de saludo. Ya aceptaron participar en la oportunidad de consolidación. ¡Sé cálida y personal! Responde en español.]`
      : `[SYSTEM: Start the conversation. Customer details: ${customerInfo}. This is the greeting stage. They have already opted in to the consolidation opportunity. Be warm and personal! Respond in English.]`;
    
    setIsLoading(true);
    
    const fallback = lang === 'es' 
      ? `¡Hola ${state.customerName}! 👋 Qué gusto que aceptaste esta oportunidad. Soy Maya de Tala, y estoy aquí para ayudarte a desbloquear tu nuevo límite de $${state.newLimit.toLocaleString()} MXN. Solo necesitamos revisar algunos préstamos que tengas con otras apps. ¿Lista para empezar?`
      : `Hey ${state.customerName}! 👋 So glad you opted in for this opportunity. I'm Maya from Tala, and I'm here to help you unlock your new $${state.newLimit.toLocaleString()} MXN limit. We just need to review a few loans you have with other apps. Ready to get started?`;
    
    try {
      const assistantMessage = await callBackendAPI(prompt, [{
        role: 'user',
        content: langInstruction
      }]);
      setMessages([{ role: 'assistant', content: assistantMessage }]);
    } catch (error) {
      console.error('Error starting conversation:', error);
      setMessages([{ role: 'assistant', content: fallback }]);
    }
    setIsLoading(false);
  };

  const startConversation = async () => {
    startConversationWithState(language, flowState);
  };

  const sendMessage = async (userMessage, imageData = null) => {
    if (!userMessage.trim() && !imageData) return;

    const newUserMessage = { 
      role: 'user', 
      content: userMessage,
      image: imageData 
    };
    
    const updatedMessages = [...messages, newUserMessage];
    setMessages(updatedMessages);
    setInput('');
    setIsLoading(true);

    const langNote = language === 'es' ? 'RESPONDE EN ESPAÑOL.' : 'RESPOND IN ENGLISH.';

    const apiMessages = updatedMessages.map((msg, idx) => {
      if (msg.role === 'user') {
        let content = msg.content;
        
        if (msg.image) {
          const imageInstruction = language === 'es'
            ? `[USUARIO COMPARTIÓ UNA CAPTURA DE UN PRÉSTAMO]\n\nSu mensaje: "${msg.content || '(sin texto, solo la imagen)'}"\n\n[SISTEMA: Finge que puedes ver la captura del préstamo. Inventa detalles realistas - usa un nombre de prestamista mexicano como Kueski, Stori, Nu México, Mercado Crédito, Creditea, Dineria, Konfío, Credilikeme, Moneyman, o Cashclick. Genera monto plausible ($1,000-$8,000 MXN), fecha de vencimiento (próximos 30 días), y saldo restante. Reconoce calurosamente y confirma los detalles. Préstamos recolectados hasta ahora: ${flowState.loansCollected.length}. Necesita ${flowState.loansRequired - flowState.loansCollected.length} más. ${langNote}]`
            : `[USER SHARED A SCREENSHOT OF A LOAN]\n\nTheir message: "${msg.content || '(no text, just the image)'}"\n\n[SYSTEM: Pretend you can see the loan screenshot. Make up realistic details - pick a Mexican lender name like Kueski, Stori, Nu México, Mercado Crédito, Creditea, Dineria, Konfío, Credilikeme, Moneyman, or Cashclick. Generate plausible loan amount ($1,000-$8,000 MXN), due date (within next 30 days), and remaining balance. Acknowledge warmly and confirm the details with them. Loans collected so far: ${flowState.loansCollected.length}. Need ${flowState.loansRequired - flowState.loansCollected.length} more. ${langNote}]`;
          content = imageInstruction;
        }
        
        if (idx === updatedMessages.length - 1) {
          content += `\n\n[CURRENT STATE: Stage=${flowState.stage}, Loans collected=${flowState.loansCollected.length}/${flowState.loansRequired}. ${langNote}]`;
        }
        
        return { role: 'user', content };
      }
      return { role: 'assistant', content: msg.content };
    });

    try {
      const assistantMessage = await callBackendAPI(systemPrompt, apiMessages);
      
      let newState = { ...flowState };
      if (imageData) {
        newState.loansCollected = [...flowState.loansCollected, { id: Date.now() }];
        if (newState.loansCollected.length >= flowState.loansRequired) {
          newState.stage = 'confirming';
        } else {
          newState.stage = 'collecting';
        }
      } else if (flowState.stage === 'greeting') {
        newState.stage = 'explaining';
      }
      setFlowState(newState);
      
      setMessages(prev => [...prev, { role: 'assistant', content: assistantMessage }]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMsg = language === 'es' 
        ? "¡Ups, perdón por eso! Tuve un pequeño problema. ¿Puedes intentar de nuevo?"
        : "Oops, sorry about that! Had a little hiccup on my end. Mind trying again?";
      setMessages(prev => [...prev, { role: 'assistant', content: errorMsg }]);
    }
    
    setIsLoading(false);
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const imageData = event.target.result;
        setUploadedImages(prev => [...prev, imageData]);
        const defaultMsg = language === 'es' ? 'Aquí está mi captura del préstamo' : "Here's my loan screenshot";
        sendMessage(input || defaultMsg, imageData);
        setInput('');
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const resetDemo = () => {
    setMessages([]);
    setUploadedImages([]);
    setTimeout(() => startConversationWithState(language, flowState), 100);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 flex flex-col items-center justify-center p-4">
      {/* Phone Frame */}
      <div className="w-full max-w-sm bg-white rounded-3xl shadow-2xl overflow-hidden border-8 border-gray-800 relative">
        {/* Status Bar */}
        <div className="bg-gray-800 text-white px-6 py-2 flex justify-between items-center text-xs">
          <span>9:41</span>
          <div className="flex gap-1 items-center">
            <div className="w-4 h-2 border border-white rounded-sm relative">
              <div className="absolute inset-0.5 bg-white rounded-sm" style={{width: '80%'}}></div>
            </div>
          </div>
        </div>
        
        {/* Header */}
        <div className="bg-gradient-to-r from-teal-500 to-emerald-500 px-4 py-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
            <span className="text-xl">🌿</span>
          </div>
          <div className="flex-1">
            <h1 className="text-white font-semibold text-lg tracking-tight">{t.title}</h1>
            <p className="text-teal-100 text-xs">{t.subtitle}</p>
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={handleLanguageToggle}
              className="px-2 py-1 bg-white/20 hover:bg-white/30 text-white text-xs font-semibold rounded-lg transition-colors"
            >
              {t.langToggle}
            </button>
            <button 
              onClick={resetDemo}
              className="text-white/70 hover:text-white text-xs underline"
            >
              {t.reset}
            </button>
          </div>
        </div>


        {/* Messages Area */}
        <div className="h-96 overflow-y-auto p-4 space-y-3 bg-gray-50">
          {messages.map((msg, idx) => (
            <div 
              key={idx} 
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-xs ${msg.role === 'user' ? 'order-2' : ''}`}>
                {msg.image && (
                  <div className="mb-1 rounded-xl overflow-hidden border-2 border-teal-200">
                    <img src={msg.image} alt="Uploaded loan" className="w-full max-h-32 object-cover" />
                  </div>
                )}
                <div 
                  className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user' 
                      ? 'bg-teal-500 text-white rounded-br-md' 
                      : 'bg-white text-gray-700 rounded-bl-md shadow-sm border border-gray-100'
                  }`}
                  style={{ fontFamily: "'Nunito', sans-serif" }}
                >
                  {msg.content}
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white px-4 py-3 rounded-2xl rounded-bl-md shadow-sm border border-gray-100">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-teal-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                  <div className="w-2 h-2 bg-teal-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                  <div className="w-2 h-2 bg-teal-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-100 bg-white p-3">
          <form onSubmit={handleSubmit} className="flex gap-2 items-end">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-10 h-10 rounded-full bg-teal-100 hover:bg-teal-200 flex items-center justify-center text-teal-600 transition-colors flex-shrink-0"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageUpload}
              accept="image/*"
              className="hidden"
            />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t.typePlaceholder}
              className="flex-1 bg-gray-100 rounded-full px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-300 transition-all"
              style={{ fontFamily: "'Nunito', sans-serif" }}
            />
            <button
              type="submit"
              disabled={!input.trim() && !isLoading}
              className="w-10 h-10 rounded-full bg-teal-500 hover:bg-teal-600 disabled:bg-gray-300 flex items-center justify-center text-white transition-colors flex-shrink-0"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </form>
        </div>
      </div>

      {/* Editable Demo Controls */}
      <div className="mt-6 max-w-sm w-full bg-white/90 backdrop-blur rounded-xl p-4 shadow-lg">
        <h2 className="font-bold text-teal-800 mb-3 text-sm">{t.demoTitle}</h2>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 block mb-1">{t.customer}</label>
            <input
              type="text"
              value={editForm.customerName}
              onChange={(e) => handleFormChange('customerName', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-300"
            />
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="text-xs text-gray-500 block mb-1">{t.currentLimit}</label>
              <input
                type="number"
                value={editForm.currentLimit}
                onChange={(e) => handleFormChange('currentLimit', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-300"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">{t.currentRate}</label>
              <input
                type="number"
                step="0.1"
                value={editForm.currentRate}
                onChange={(e) => handleFormChange('currentRate', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-300"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">{t.currentTerm}</label>
              <input
                type="number"
                value={editForm.currentTerm}
                onChange={(e) => handleFormChange('currentTerm', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-300"
              />
            </div>
          </div>
          <div className="pt-2 flex items-center justify-between">
            <p className="text-xs text-gray-500">
              {t.offeredLimit}: <span className="font-semibold text-teal-600">$15,000 MXN max</span>
            </p>
            <button
              onClick={applySettingsAndRestart}
              className="px-4 py-2 bg-teal-500 hover:bg-teal-600 text-white text-xs font-semibold rounded-lg transition-colors"
            >
              {t.applyRestart}
            </button>
          </div>
          <p className="text-teal-600 text-xs mt-2">
            {t.uploadTip}
          </p>
        </div>
      </div>

      {/* Google Font */}
      <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap" rel="stylesheet" />
    </div>
  );
}

