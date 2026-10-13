# Multi-Tool AI Agent for Bangladesh

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Udipto-Mondal/Project-Multi-Tool-AI-Agent-for-Bangladesh/blob/main/notebooks/Bangladesh_MultiTool_AI_Agent_Demo.ipynb)
[![Tests Passing](https://img.shields.io/badge/tests-18%20passed-brightgreen.svg)](tests/)

A multi-tool AI assistant built with **LangChain** to answer both structured, domain-specific data queries across three Bangladesh datasets and general knowledge questions via real-time web search.

---

## Architecture Overview

```text
                                  User Query
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │    BangladeshAIAgent      │
                        │ (LangChain AgentExecutor) │
                        └─────────────┬─────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
      [Education Data]        [Healthcare Data]         [Dining Data]
              ▼                       ▼                       ▼
    ┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
    │InstitutionsDBTool │   │  HospitalsDBTool  │   │ RestaurantsDBTool │
    └─────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘
              │                       │                       │
              ▼                       ▼                       ▼
      institutions.db            hospitals.db          restaurants.db
       (34,901 rows)            (38,886 rows)          (10,758 rows)
              │                       │                       │
              └───────────────────────┼───────────────────────┘
                                      │
                       [General Knowledge / Policies]
                                      ▼
                            ┌───────────────────┐
                            │   WebSearchTool   │
                            └─────────┬─────────┘
                                      │
                                      ▼
                          Live Web Search Engine
                         (DuckDuckGo / Tavily)
```

---

## Datasets & SQLite Database Schemas

The system converts three datasets from HuggingFace into normalized, indexed SQLite databases:

### 1. `institutions.db` (Table: `institutions`)
* **Source:** [Mahadih534/Institutional-Information-of-Bangladesh](https://huggingface.co/datasets/Mahadih534/Institutional-Information-of-Bangladesh)
* **Total Records:** 34,901
* **Key Columns:**
  * `id` (INTEGER PRIMARY KEY)
  * `name` (TEXT) - Institution name
  * `eiin` (INTEGER) - Educational Institute Identification Number
  * `type` (TEXT) - College, School, Madrasha, University
  * `division` (TEXT) - Administrative division (e.g., Dhaka, Chittagong, Rajshahi)
  * `district` (TEXT) - District
  * `thana` (TEXT) - Upazila/Thana
  * `management_type` (TEXT) - Government or Non-Government
  * `education_level` (TEXT) - Higher Secondary, Secondary, Degree, etc.
  * `mpo_status` (TEXT) - MPO inclusion status (YES/NO)

### 2. `hospitals.db` (Table: `hospitals`)
* **Source:** [Mahadih534/all-bangladeshi-hospitals](https://huggingface.co/datasets/Mahadih534/all-bangladeshi-hospitals)
* **Total Records:** 38,886
* **Key Columns:**
  * `id` (INTEGER PRIMARY KEY)
  * `name` (TEXT) - Healthcare facility name
  * `name_bn` (TEXT) - Bengali facility name
  * `code` (INTEGER) - Facility identification code
  * `agency` (TEXT) - Administrative body (e.g., DGHS, DGFP)
  * `type` (TEXT) - District Hospital, Upazila Health Complex, Community Clinic, Private Hospital
  * `division` (TEXT) - Administrative division
  * `district` (TEXT) - District
  * `upazila` (TEXT) - Upazila
  * `bed_capacity` (INTEGER) - Explicit bed capacity count
  * `is_private` (INTEGER) - 0 for Public/Government, 1 for Private

### 3. `restaurants.db` (Table: `restaurants`)
* **Source:** [Mahadih534/Bangladeshi-Restaurant-Data](https://huggingface.co/datasets/Mahadih534/Bangladeshi-Restaurant-Data)
* **Total Records:** 10,758 (deduplicated)
* **Key Columns:**
  * `id` (INTEGER PRIMARY KEY)
  * `place_id` (TEXT) - Google Places identifier
  * `name` (TEXT) - Restaurant name
  * `latitude` / `longitude` (REAL) - Coordinates
  * `rating` (REAL) - Customer rating (0.0 to 5.0)
  * `reviews_count` (INTEGER) - Total review count
  * `price_level` (INTEGER) - Relative affluence scale (1-4)
  * `location` (TEXT) - City/district extracted from address
  * `address` (TEXT) - Full street address

---

## Tools Specification

All tools inherit from LangChain's `BaseTool` interface:

| Tool Name | Target Domain | Backend | Sample Query |
| :--- | :--- | :--- | :--- |
| **`InstitutionsDBTool`** | Universities, colleges, schools, madrasahs | `institutions.db` | *"How many colleges are in Dhaka?"* |
| **`HospitalsDBTool`** | Healthcare facilities, clinics, bed counts | `hospitals.db` | *"How many hospitals are in Dhaka?"* |
| **`RestaurantsDBTool`** | Restaurants, ratings, reviews, dining | `restaurants.db` | *"Top rated restaurants in Dhaka"* |
| **`WebSearchTool`** | Live definitions, policies, cultural context | DuckDuckGo / Tavily | *"What is the role of DGHS in Bangladesh?"* |

---

## Project Structure

```text
Project-Multi-Tool-AI-Agent-for-Bangladesh/
├── data/
│   ├── institutions.db
│   ├── hospitals.db
│   └── restaurants.db
├── notebooks/
│   └── Bangladesh_MultiTool_AI_Agent_Demo.ipynb
├── scripts/
│   ├── download_data.py
│   ├── build_databases.py
│   └── make_colab_notebook.py
├── src/
│   ├── config.py
│   ├── agent/
│   │   ├── __init__.py
│   │   └── main_agent.py
│   └── tools/
│       ├── __init__.py
│       ├── base_db_tool.py
│       ├── institutions_tool.py
│       ├── hospitals_tool.py
│       ├── restaurants_tool.py
│       └── search_tool.py
├── tests/
│   ├── test_databases.py
│   ├── test_tools.py
│   ├── test_search.py
│   └── test_agent.py
├── .env.example
├── .gitignore
├── requirements.txt
├── main.py
└── README.md
```

---

## Setup & Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/Udipto-Mondal/Project-Multi-Tool-AI-Agent-for-Bangladesh.git
cd Project-Multi-Tool-AI-Agent-for-Bangladesh
```

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Environment Configuration (Optional)
Copy `.env.example` to `.env` to configure LLM and search keys if desired:
```bash
cp .env.example .env
```
* `GOOGLE_API_KEY`: Enables Google Gemini LLM reasoning.
* `TAVILY_API_KEY`: Optional Tavily search key (DuckDuckGo works out of the box with zero keys required).

---

## Usage Guide

### 1. Running the Predefined Demo Suite
```bash
python main.py --demo
```

### 2. Asking a Single Query via CLI
```bash
# Healthcare query (routed to HospitalsDBTool)
python main.py --query "How many hospitals are in Dhaka?"

# Education query (routed to InstitutionsDBTool)
python main.py --query "How many colleges are in Dhaka?"

# Restaurant query (routed to RestaurantsDBTool)
python main.py --query "Top rated restaurants in Dhaka"

# Policy / General Knowledge query (routed to WebSearchTool)
python main.py --query "What is the role of DGHS in Bangladesh?"
```

### 3. Interactive Shell Mode
```bash
python main.py --interactive
```

### 4. Running the Complete Automated Test Suite
```bash
python -m pytest tests/ -v
```

---

## Google Colab Demo

An end-to-end interactive notebook is available for instant demonstration in Google Colab:

👉 **[Open in Google Colab](https://colab.research.google.com/github/Udipto-Mondal/Project-Multi-Tool-AI-Agent-for-Bangladesh/blob/main/notebooks/Bangladesh_MultiTool_AI_Agent_Demo.ipynb)**

---

## License

This project is licensed under the MIT License.
