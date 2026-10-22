# TN Scheme AI – Tamil Nadu Government Scheme Assistant

TN Scheme AI is an AI-powered web application that helps users explore Tamil Nadu government schemes and understand their eligibility criteria, benefits, and required documents.

The application uses Retrieval-Augmented Generation (RAG) to retrieve relevant information from indexed scheme documents and Google Gemini to generate clear, context-based answers. Users can register, log in, and interact with the assistant through a simple chat interface.

## Features

- User registration and login
- JWT-based authentication
- AI-powered question answering using Google Gemini
- Semantic search using ChromaDB
- Retrieval-Augmented Generation (RAG)
- Relevant source information in responses
- React-based chat interface
- Deployed frontend and backend

## Tech Stack

**Frontend:** React.js, Vite, CSS  
**Backend:** Python, FastAPI  
**AI:** Google Gemini API  
**Vector Database:** ChromaDB  
**Authentication:** JWT, password hashing  
**Deployment:** Vercel, Render

## How It Works

1. The user registers or logs in to the application.
2. The user asks a question about a Tamil Nadu government scheme.
3. The backend searches indexed documents for relevant information using ChromaDB.
4. The retrieved context is passed to Google Gemini.
5. The assistant generates an answer based on the retrieved information and returns it to the user.

## Live Demo

- **Frontend:** https://tn-scheme-ai.vercel.app
- **Backend API:** https://tn-scheme-ai.onrender.com
- **API Documentation:** https://tn-scheme-ai.onrender.com/docs

## Running Locally

### Prerequisites

- Python installed
- Node.js and npm installed
- Google Gemini API key

### Backend Setup

1. Clone the repository.

   ```bash
   git clone <YOUR_GITHUB_REPOSITORY_URL>
   ```

2. Navigate to the backend directory and install the dependencies.

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the backend directory.

   ```env
   GEMINI_API_KEY=your_gemini_api_key
   JWT_SECRET_KEY=your_secure_secret_key
   ```

4. Start the FastAPI server using the command appropriate for your project structure.

   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory.
2. Install the dependencies.

   ```bash
   npm install
   ```

3. Configure the frontend API URL in `.env`:

   ```env
   VITE_API_URL=http://localhost:8000
   ```

4. Start the development server.

   ```bash
   npm run dev
   ```

Make sure the backend is running and the required scheme documents and ChromaDB collection are available before testing the chat functionality.

## Security Notes

- Keep API keys and JWT secrets private.
- Do not commit `.env` files containing secrets.
- Configure CORS to allow only trusted frontend origins.
- Use HTTPS for deployed services.

## Limitations

The quality of answers depends on the information available in the indexed documents. Users should verify scheme eligibility, benefits, and application procedures through official government sources.

## Future Improvements

- Expand the collection of verified government scheme documents.
- Add multilingual support for Tamil and English.
- Improve source links and scheme-specific filtering.
- Add automated testing and monitoring.

---

Developed as a project to make government scheme information easier to explore using AI and semantic search.
