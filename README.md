<div align="center">
  <h1>🚀 Velocity AI</h1>
  <p><strong>Your Ultimate Personal & Workspace Productivity Co-Pilot</strong></p>
</div>

Velocity AI is a comprehensive productivity assistant designed for student founders, builders, and fast-moving teams. It intelligently monitors your tools, prioritizes your tasks, and acts as an autonomous agent to schedule blocks and pull data across multiple platforms.

---

## ✨ Features

### 🏢 Two Operating Modes
- **Personal Mode:** Tailored for student founders. Re-prioritize your academic schedule, set focus blocks for assignments, and seamlessly pivot to startup tasks.
- **Workspace Mode:** Tailored for startup teams. Get quick summaries of GitHub PRs, Slack discussions, Google Workspace updates, and cross-reference context fast.

### 🤖 Intelligent LangGraph Orchestration
Velocity AI isn't incredibly static; it runs on dynamically routed agent graphs leveraging `LangGraph` and `Langchain`, utilizing the lightning-fast **Groq (Llama 3.3 70B)** reasoning models to handle multi-step planning, background polling, and data fetching on your behalf.

### 🔌 Ecosystem Integrations
- **GitHub:** Reads latest commits, merges, and issues.
- **Slack:** Polls recent conversations tracking unread mentions across active channels natively.
- **Google Workspace:** Incorporates Docs, Calendar, and Gmail integration to read context and inject schedule blockers natively into your calendar.
- **Jira / Linear (Mocked)**: Pull project tickets dynamically.

### 🧠 Advanced RAG & Long-term Memory
- **MongoDB Checkpointer**: Saves conversation threads so the agent remembers previous steps natively without restarting.
- **Neo4j Graph Database**: Maps structured entities and conceptual data using GraphRAG methodologies to power intelligent, deeper context insights across your workspace.

---

## 🏗 Architecture & Tech Stack

**Frontend**
*   **Framework:** React 18 + Vite
*   **Styling:** Tailwind CSS + \`lucide-react\` icons
*   **Language:** TypeScript
*   **Routing:** React Router v6

**Backend**
*   **Framework:** FastAPI (Python)
*   **AI Models:** Groq \`llama-3.3-70b-versatile\`
*   **Orchestration:** LangChain / LangGraph
*   **Databases:** MongoDB (Agent Memory Checkpoints) & Neo4j (Graph Database)

---

## 🛠 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Active MongoDB and Neo4j instances
- [Groq API Key](https://console.groq.com/) for Free AI endpoints.

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Velocity-AI.git
cd Velocity-AI
```

### 2. Backend Setup
Set up your virtual environment and install dependencies:
```bash
cd backend
conda create -n velocity python=3.11
conda activate velocity
pip install -r requirements.txt
```

Set up your `.env` file in the `/backend` directory:
```env
# Groq AI
GROQ_API_KEY=your_groq_api_key_here

# MongoDB
MONGODB_URI=mongodb+srv://...

# Neo4j
NEO4J_URI=neo4j+s://...
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

Start the FastAPI server:
```bash
python main.py
```
*(The backend runs primarily on `http://localhost:8000`)*

### 3. Frontend Setup
Open a new terminal and navigate to the `/frontend` directory:
```bash
cd frontend
npm install
```

Start the Vite development server:
```bash
npm run dev
```
*(The frontend runs primarily on `http://localhost:5173`)*

---

## 🤝 Contributing
Want to add more tools to the LangGraph execution flow? Contributions are welcome! Please fork the repository, make your changes on a separate functional branch, and submit a pull request down the line.

## 📄 License
This project is licensed under the [MIT License](LICENSE).
