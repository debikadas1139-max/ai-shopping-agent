# 🛒 AI Shopping Agent — Full-Stack Intelligent E-Commerce Store

An AI-powered grocery and specialty food e-commerce web application built with **React**, **FastAPI**, **LangChain**, and **Groq LLM/Vision**. Users can browse and filter a seeded product catalog, chat with an intelligent shopping assistant for personalized recommendations, search for products by uploading images, and manage their cart and orders.

---

## ✨ Key Features

- **🛍️ Interactive Product Catalog:** Browse 32+ seeded grocery items across categories (`honey`, `oil`, `nuts`, `seeds`, `grains`, `tea`, `coffee`, `snacks`, `dairy-alt`) with real-time filtering by category, maximum price, minimum customer rating, organic status, and price sorting.
- **🤖 Conversational AI Shopping Assistant:** Powered by **LangChain** and **Groq (`qwen/qwen3-32b`)** to understand natural language queries, query the live SQLite database via tool-calling, compare products, and suggest personalized recommendations.
- **📸 Visual Search (Shop by Image):** Upload a photo of any food or grocery item; a **Groq Vision model (`meta-llama/llama-4-scout-17b-16e-instruct`)** identifies the item and matches it with relevant products in the store catalog.
- **🛒 Cart & Order Management:** Add items to a persistent cart drawer with backend-calculated totals, place demo orders persisted in SQLite, and track order history in the **My Orders** view.
- **⚡ Modern Decoupled Architecture:** Fast, type-safe REST API backend with interactive Swagger documentation (`/docs`) paired with a responsive Vite + Tailwind CSS frontend.

---

## 🏗️ System Architecture

```text
┌─────────────────────────────┐         Vite Proxy (/api)         ┌─────────────────────────────┐
│     React + Vite Frontend   │ ────────────────────────────────► │     FastAPI REST Backend    │
│  (Tailwind CSS, Axios, UI)  │ ◄──────────────────────────────── │ (Pydantic, SQLAlchemy ORM)  │
└─────────────────────────────┘            JSON Responses         └──────────────┬──────────────┘
                                                                                 │
                                                    ┌────────────────────────────┼────────────────────────────┐
                                                    ▼                            ▼                            ▼
                                       ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
                                       │     SQLite Database     │  │   LangChain + Groq LLM  │  │    Groq Vision Model    │
                                       │ (Products, Cart, Orders)│  │   (qwen/qwen3-32b)      │  │ (llama-4-scout-17b)     │
                                       └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer           | Technologies                                                                        |
| :-------------- | :---------------------------------------------------------------------------------- |
| **Frontend**    | React, Vite, Tailwind CSS, Axios, Lucide React Icons                                |
| **Backend**     | Python 3.10+, FastAPI, Uvicorn, Pydantic, SQLAlchemy                                |
| **Database**    | SQLite (`store.db`)                                                                 |
| **AI & Vision** | LangChain, Groq API (`qwen/qwen3-32b`, `meta-llama/llama-4-scout-17b-16e-instruct`) |
| **Testing**     | Pytest, FastAPI TestClient                                                          |

---

## 📁 Project Structure

```text
ai-shopping-agent/
├── backend/
│   ├── app/
│   │   ├── agent/          # LangChain agent, system prompts & database search tools
│   │   ├── api/            # FastAPI route handlers (products, chat, cart, orders, vision)
│   │   ├── services/       # Business logic & Groq LLM/Vision client wrappers
│   │   ├── config.py       # Pydantic settings & environment variable loader
│   │   ├── database.py     # SQLAlchemy engine & session management
│   │   ├── main.py         # FastAPI app initialization, CORS & router registration
│   │   ├── models.py       # SQLAlchemy ORM models (Product, Order, OrderItem, Review)
│   │   └── schemas.py      # Pydantic request/response validation schemas
│   ├── scripts/
│   │   └── init_db.py      # Database table creation & 32-item catalog seeder
│   ├── tests/              # Automated API tests (test_products.py, test_cart.py, test_orders.py)
│   ├── .env                # Environment variables (excluded from Git via .gitignore)
│   └── requirements.txt    # Python package dependencies
├── frontend/
│   ├── src/                # React pages, reusable components & Axios API client
│   ├── package.json        # Frontend scripts & dependencies
│   └── vite.config.js      # Vite dev server & /api proxy configuration
├── .gitignore              # Git ignore rules for venv, node_modules, .env, store.db
└── README.md               # Project documentation
```

---

## 🔌 Core API Endpoints

Once the backend is running, interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

| Method         | Endpoint              | Description                                                                                                           |
| :------------- | :-------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| `GET`          | `/api/products`       | Fetch products with optional query filters (`category`, `max_price`, `min_rating`, `is_organic`, `search`, `sort_by`) |
| `GET`          | `/api/products/{id}`  | Retrieve detailed product info and customer reviews                                                                   |
| `POST`         | `/api/chat`           | Send a natural language message to the LangChain shopping assistant                                                   |
| `POST`         | `/api/vision/search`  | Upload an image file to identify the food item and find matching catalog products                                     |
| `POST`         | `/api/cart/calculate` | Calculate item subtotals, taxes, and final cart total                                                                 |
| `GET` / `POST` | `/api/orders`         | Retrieve order history or submit a new confirmed order                                                                |

---

## 💬 Example Prompts to Try in the AI Assistant

- _"Show me all organic honey products under $25."_
- _"What are your highest-rated nuts or seeds for healthy snacking?"_
- _"Compare your olive oils and tell me which one is best for cooking."_
- _"I'm looking for caffeine-free herbal teas under $15."_

---

## 🚀 Local Setup & Installation

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** & **npm**
- A free **Groq API Key** from [console.groq.com](https://console.groq.com)

### 1. Clone the Repository

```bash
git clone [https://github.com/YOUR_USERNAME/ai-shopping-agent.git](https://github.com/YOUR_USERNAME/ai-shopping-agent.git)
cd ai-shopping-agent
```

### 2. Backend Setup

Navigate into the `backend` directory, create a virtual environment, and install dependencies:

```bash
cd backend
python -m venv venv

# Activate virtual environment:
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file inside the `backend/` folder:

```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=qwen/qwen3-32b
GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
DATABASE_URL=sqlite:///./store.db
FRONTEND_ORIGIN=http://localhost:5173
```

Initialize and seed the SQLite database (run from inside `backend/` so `store.db` is created in the expected directory):

```bash
python scripts/init_db.py
```

Start the FastAPI server:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

_The API will be live at `http://127.0.0.1:8000`._

### 3. Frontend Setup

Open a **second terminal**, navigate to the `frontend` folder, install packages, and start the Vite development server:

```bash
cd frontend
npm install
npm run dev
```

_Open `http://localhost:5173` in your browser to use the application._

---

## 🧪 Running Tests

To run the automated backend test suite using `pytest`, navigate to the `backend/` folder with your virtual environment activated:

```bash
cd backend
pytest
```

---

## 🔮 Future Enhancements

- **User Authentication:** JWT-based user login and personalized order histories.
- **Persistent Cloud Database:** Migrate from local SQLite to PostgreSQL (e.g., Supabase or Neon) for production deployment.
- **Add-to-Cart via AI Chat:** Allow the LangChain agent to directly add recommended products into the user's active shopping cart.
- **Payment Gateway Integration:** Integrate Stripe test checkout for realistic payment flows.

---

## 📸 Screenshots

- **Grocery Catalog & Filters:** `![Catalog View](screenshots/Catalog-image.png)`
- **AI Shopping Assistant Chat:** `![AI Assistant](screenshots/Ai-assistance-image.png)`
- **Visual Search (Shop by Image):** `![Visual Search](screenshots/Image-search.png)`
