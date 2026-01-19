# 🗺️ Local Discovery Agent
> **Your Hyper-Local AI Concierge**  
> _Powered by Agno Agent (Llama 3) & Ola Maps_

## 🚀 Overview
The **Local Discovery Agent** is not just a search engine; it's an **active planner**. While general LLMs give you a list of 10 places, this agent acts as an executive assistant that **plans your entire day**.

It connects the reasoning power of **Llama 3.1** (via Groq) with the real-time, hyper-local data of **Ola Maps** to create grounded, hallucination-free itineraries.

### 🌟 Key Features
- **"Plan My Day" Button**: One click to generate a complete scheduling including dining and activities.
- **Grounded Accuracy**: Fetches real-time data from **Ola Maps** to ensure all places actually exist and are currently open.
- **Actionable Outputs**:
  - **📅 Add to Calendar**: Download an `.ics` file to block time on your schedule.
  - **📄 PDF Export**: Get a clean, shareable PDF of your plan.
- **Targeted Discovery**: Specialized for Indian cities (started with Bangalore) using local datasets.

## 🏗️ Architecture
This project implements an **Agentic AI** workflow:
1.  **User Intent**: Captures preferences (Cuisine, Activities, Location) via **Streamlit**.
2.  **Reasoning (The Brain)**: The **Agno Agent** analyzes the request and decides the strategy.
3.  **Action (The Tools)**: The Agent autonomously calls `search_places` (Ola Maps API) to find real locations.
4.  **Synthesis**: Data is filtered, ranked, and compiled into a structured itinerary.

## ⚡ Quick Start

### Prerequisites
- Python 3.9+
- [Ola Maps API Key](https://maps.olamaps.io/)
- [Groq API Key](https://console.groq.com/)

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/ananttewari/Local-Discovery-Agent.git
    cd Local-Discovery-Agent
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment Variables**
    Create a `.env` file in the root directory:
    ```ini
    OLA_MAPS_API_KEY=your_ola_maps_key_here
    GROQ_API_KEY=your_groq_api_key_here
    ```

4.  **Run the Application**
    ```bash
    streamlit run app.py
    ```

## 🎮 Usage
1.  Open the app in your browser (usually `http://localhost:8501`).
2.  **Select Preferences**: Choose your favorite cuisines and activities from the sidebar.
3.  **Choose Location**: Pick a popular area (e.g., Koramangala, Indiranagar).
4.  Click **"Plan My Day 🚀"**.
5.  View the generated itinerary and **Download PDF/Calendar** to save it.

## 💡 Why Agentic AI?
| Feature | ChatGPT (General LLM) | Local Discovery Agent (This Project) |
| :--- | :--- | :--- |
| **Data Source** | Static Training Data (Cutoff dates) | **Real-time API (Ola Maps)** |
| **Accuracy** | Can "hallucinate" fake addresses | **Grounded**: Verified existence via Map tools |
| **Output** | Text / Conversation | **Structured Files**: PDFs & Calendar events |

---
*Built with ❤️ by Anant Tewari*