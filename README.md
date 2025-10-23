# Business Partner AI Demo

An AI-powered business partner that helps small business owners get loans and grow their businesses through personalized coaching.

## 🚀 Live Demo

- **Frontend**: [GitHub Pages URL - will be added after deployment]
- **Backend**: [Vercel URL - will be added after deployment]

## 📁 Project Structure

```
.
├── msme-assistant.html          # Frontend chat interface
├── backend/                     # Backend API proxy
│   ├── server.js               # Express server
│   ├── package.json            # Dependencies
│   ├── vercel.json             # Vercel config
│   └── README.md               # Backend documentation
├── QUICK_START.md              # Quick deployment guide
└── README.md                   # This file
```

## 🎯 Features

- **Smart Onboarding**: Conversational loan application process
- **Photo Analysis**: Upload business photos for personalized insights
- **Business Coaching**: AI-powered advice on sales, cash flow, marketing, and more
- **Loan Management**: Track loan status and payments
- **Computer Vision**: Analyzes business photos to provide specific recommendations

## 🛠️ Tech Stack

- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Backend**: Node.js, Express
- **AI**: Anthropic Claude API (Sonnet 4)
- **Hosting**: GitHub Pages (frontend) + Vercel (backend)

## 📦 Setup & Deployment

See [QUICK_START.md](QUICK_START.md) for detailed deployment instructions.

### Quick Deploy

1. **Backend to Vercel**:
   ```bash
   cd backend
   vercel --prod
   ```

2. **Frontend to GitHub Pages**:
   - Push this repo to GitHub
   - Enable GitHub Pages in Settings
   - Update the API_URL in `msme-assistant.html` with your Vercel URL

## 🔒 Security

- API keys are stored securely in Vercel environment variables
- Backend acts as a proxy to protect credentials
- No sensitive data in frontend code

## 💰 Costs

- **Hosting**: Free (GitHub Pages + Vercel hobby tier)
- **API Usage**: ~$0.01 per conversation

## 📝 License

This is a demo/prototype application.

## 🤝 Contributing

This is a demonstration project. Feel free to fork and adapt for your needs.
