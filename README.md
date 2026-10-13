# Multi-Tool AI Agent for Bangladesh

A modular multi-tool AI assistant designed to answer structured domain queries and general knowledge questions about Bangladesh. The agent bridges offline relational intelligence across three national datasets with real-time web search capabilities.

---

## Datasets & Database Schemas

The project converts three authentic HuggingFace datasets into optimized SQLite databases:

### 1. `institutions.db` (Table: `institutions`)
* **Source:** [Mahadih534/Institutional-Information-of-Bangladesh](https://huggingface.co/datasets/Mahadih534/Institutional-Information-of-Bangladesh)
* **Total Records:** 34,901
* **Key Columns:**
  * `id` (INTEGER PRIMARY KEY)
  * `name` (TEXT) - Name of educational/governmental institution
  * `eiin` (INTEGER) - Educational Institute Identification Number
  * `type` (TEXT) - Institution type (College, School, Madrasha, etc.)
  * `division` (TEXT) - Administrative division
  * `district` (TEXT) - District
  * `thana` (TEXT) - Upazila/Thana
  * `management_type` (TEXT) - Government or Non-Government
  * `education_level` (TEXT) - Education level offered
  * `mpo_status` (TEXT) - Monthly Pay Order affiliation status

### 2. `hospitals.db` (Table: `hospitals`)
* **Source:** [Mahadih534/all-bangladeshi-hospitals](https://huggingface.co/datasets/Mahadih534/all-bangladeshi-hospitals)
* **Total Records:** 38,886
* **Key Columns:**
  * `id` (INTEGER PRIMARY KEY)
  * `name` (TEXT) - Healthcare facility name
  * `agency` (TEXT) - Administrative agency (e.g., DGHS)
  * `type` (TEXT) - Facility type (District Hospital, Upazila Health Complex, Clinic, etc.)
  * `division` (TEXT) - Division
  * `district` (TEXT) - District
  * `upazila` (TEXT) - Upazila
  * `bed_capacity` (INTEGER) - Derived bed capacity where explicitly defined
  * `is_private` (INTEGER) - 0 for public/governmental, 1 for private

### 3. `restaurants.db` (Table: `restaurants`)
* **Source:** [Mahadih534/Bangladeshi-Restaurant-Data](https://huggingface.co/datasets/Mahadih534/Bangladeshi-Restaurant-Data)
* **Total Records:** 10,758 (deduplicated)
* **Key Columns:**
  * `id` (INTEGER PRIMARY KEY)
  * `place_id` (TEXT) - Google Places identifier
  * `name` (TEXT) - Restaurant name
  * `rating` (REAL) - Customer rating score
  * `reviews_count` (INTEGER) - Total review count
  * `price_level` (INTEGER) - Relative affluence/pricing scale (1-4)
  * `location` (TEXT) - City/district extracted from address
  * `address` (TEXT) - Full street address
  * `latitude` / `longitude` (REAL) - Geographic coordinates

---

## Project Structure

```text
Project-Multi-Tool-AI-Agent-for-Bangladesh/
├── data/
│   ├── institutions.db
│   ├── hospitals.db
│   └── restaurants.db
├── scripts/
│   ├── download_data.py
│   └── build_databases.py
├── src/
│   ├── config.py
│   ├── tools/
│   │   ├── institutions_tool.py
│   │   ├── hospitals_tool.py
│   │   ├── restaurants_tool.py
│   │   └── search_tool.py
│   └── agent/
│       └── main_agent.py
├── tests/
│   └── test_databases.py
├── .env.example
├── .gitignore
├── requirements.txt
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

### 3. Build / Verify Databases
To download the raw CSVs and regenerate the SQLite databases with indexes:
```bash
python scripts/download_data.py
python scripts/build_databases.py
```

### 4. Run Automated Database Verification
```bash
python -m pytest tests/test_databases.py -v
```

---

## Roadmap

- [x] **Part 1:** Convert CSV datasets to normalized, indexed SQLite databases.
- [ ] **Part 2:** Implement domain-specific LangChain database query tools (`InstitutionsDBTool`, `HospitalsDBTool`, `RestaurantsDBTool`).
- [ ] **Part 3:** Implement web search integration (`WebSearchTool`) for contextual and real-time queries.
- [ ] **Part 4:** Build the unified LangChain Agent Executor with routing logic, interactive CLI, and demo tests.
