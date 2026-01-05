# 🧭 CompassGenie

**CompassGenie** is an intelligent "All-in-One" decision engine. Unlike static map tools, CompassGenie leverages Large Language Models (LLMs) and a stateful graph workflow to interpret natural language queries, perform multi-step location searches, calculate routes, and provide real-time environmental data like Air Quality Index (AQI), weather, etc.
> "Plan my afternoon in South Delhi. I need to find a leather purse under ₹500, avoid high-pollution areas, and finish at a cafe with good Wi-Fi." — **CompassGenie orchestrates the rest.**

---

## ✨ Key Capabilities

* **🤖 State-Aware Agent:** Leveraged by **LangGraph** to maintain conversation state, enabling the AI to "reason" and iterate before selecting the appropriate tool.
* **📍 Precision Geospatial Tools:** Purpose-built integration for Google Maps Text Search, Polyline decoding, and Geocoding for high-accuracy location data.
* **🍃 Environmental Intelligence:** Real-time retrieval of the Air Quality Index (AQI) via the Google Air Quality API, paired with automated health recommendations.
* **🗺️ Dynamic Frontend:** A responsive JavaScript/Tailwind UI that dynamically renders markers and route polylines based on AI-extracted `map_data`.
* **🚦 Traffic-Aware Routing:** Calculates distance and ETA while generating AI-driven traffic tips tailored to specific route conditions.

---

## 📺 Live Demo

Experience **CompassGenie** in action! Watch how the agent processes natural language queries, interacts with geospatial tools, and renders dynamic routes in real-time.

[![CompassGenie Demo Video](https://img.youtube.com/vi/yTG3I_SE8e0/0.jpg)](https://www.youtube.com/watch?v=yTG3I_SE8e0)

> 🔗 **Direct Link:** [Watch the demo on YouTube](https://www.youtube.com/watch?v=yTG3I_SE8e0)
---


## 🏗️ System Architecture

CompassGenie is built on a **Modular Agentic Architecture**. Instead of a linear script, it uses a state-machine logic to "reason" through user requests.

### 1. Frontend (Vanilla JS + Tailwind)
Captures real-time GPS coordinates and natural language input. It handles the visualization of decoded polylines and interactive map markers.

### 2. API Layer (FastAPI)
Acts as the bridge between the client and the agent. It manages:
* **Validation:** Ensuring data integrity via Pydantic models.
* **Security:** Managing Cross-Origin Resource Sharing (CORS) and API health.

### 3. Agent Logic (LangGraph + Gemini)
The "brain" of the operation uses a cyclic graph logic:
* **Node 1 (Agent):** Analyzes the user's intent and decides if a specific tool (Maps, AQI, etc.) is required.
* **Node 2 (Tools):** Executes specialized Python functions (e.g., `get_aqi`, `maps_api_search`) to fetch real-world data.
* **The Loop:** The agent can call multiple tools in sequence, synthesizing all gathered data before returning a final, actionable answer to the user.

---

## 🛠️ The Tech Stack

| Layer | Technology              | Key Rationale |
| :--- |:------------------------| :--- |
| **Language** | Python 3.12             | Utilized for optimized memory management. |
| **Framework** | FastAPI                 | Asynchronous endpoints for high-speed AI streaming. |
| **AI Engine** | Google Gemini 2.5 Flash | Chosen for low latency and high reasoning capability. |
| **Orchestration** | LangGraph & LangChain   | Manages complex agentic "thinking" loops and state. |
| **Infrastructure** | Docker                  | Containerized for "deploy-anywhere" capability. |
---

## 🌟 Key Capabilities

* **💰 Constraint-Based Commerce:** Integrates budget filtering directly into geospatial searches. Find products within a specific price range in the real world.
* **📅 Dynamic Itinerary Planning:** Generates full-day schedules based on your current `lat, lng`, current time, and weather constraints.
* **🍃 Environmental Shield:** Automatically overlays Air Quality Index (AQI) and weather data onto suggested routes.
* **🗺️ Map-Centric Synthesis:** Converts abstract AI text into visual coordinates, markers, and route polylines.

---

## 🛠️ Installation & Setup

### 1. Clone & Setup
```powershell
git clone [https://github.com/your-username/CompassGenie.git](https://github.com/your-username/CompassGenie.git)
cd CompassGenie
```
### 2. Configuration (.env)
Create a .env file in the root directory and add your keys:
```powershell
GEMINI_API_KEY=your_gemini_key_here
MAPS_API_KEY=your_google_maps_key_here
```
### 3. Launch
**Using Docker (Recommended):**
```powershell
make build
```
**Using Local Python 3.12:**
```powershell
make install
make dev
```

---

## 🔌 API Endpoints (V1)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check and dependency verification. |
| `POST` | `/chat` | Main agent endpoint. Accepts user message + location data. |

---

## 🚀 Future Roadmap

* **🎙️ Voice Integration:** Implementation of Whisper/WebSpeech API for hands-free "Drive Mode" concierge service.
* **💾 User Preference Memory:** Long-term memory storage (PostgreSQL/MongoDB) to remember user preferences like budget, dietary restrictions, etc. This is being built as a standalone module: [PreFlex](https://github.com/ammu36/PreFlex.git).
* **⚡ Optimized Inference Speed:** Implementation of **Server-Sent Events (SSE)** and Token Streaming to provide near-instantaneous UI updates as the AI "thinks."

---
## 🧪 Quality Assurance

CompassGenie is built to be resilient, maintainable, and cost-effective. We use industry-standard tooling to ensure the concierge logic remains reliable as the project grows.

* **Unit Tests:** Core tools (AQI, Maps, Budget Filter) are validated using `pytest` to ensure logic accuracy.
* **Linting & Formatting:** [Ruff](https://github.com/astral-sh/ruff) is used to maintain strict **PEP 8** compliance, ensuring clean, readable, and standardized Python code.



```bash
# Run the full test suite
make test
```