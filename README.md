# 🕊️🚫 PigeonFree

> **Pigeon-free routes in Kazan, Russia**
> A pedestrian navigation system that predicts and helps users avoid areas with a high presence of pigeons using Machine Learning, real geolocated data, and real-time weather information.

---

## 🌟 What is PigeonFree?

PigeonFree is a web application that helps people with columbiphobia, or fear of pigeons, plan safer walking routes in Kazan by avoiding areas with high concentrations of pigeons.

The system combines:

- **357 real pigeon sighting locations** from iNaturalist and eBird
- A **Random Forest Machine Learning model** with a ROC-AUC score of 0.997
- **Real-time weather data** through Open-Meteo
- **Urban data** from OpenStreetMap, including restaurants, transport stations, parks, and other points of interest
- **Real-time community reports** submitted by users

---

## 🎯 Main Features

| Feature                 | Description                                                             |
| ----------------------- | ----------------------------------------------------------------------- |
| 🗺️ Interactive map      | Risk zones displayed according to their ML-generated probability        |
| 🤖 ML prediction        | Calibrated Random Forest model with a ROC-AUC score of 0.997            |
| 🌤️ Real-time weather    | Open-Meteo API for temperature, rain, wind, and other conditions        |
| 🚶 Walking routes       | Self-hosted OSRM server configured with pedestrian data for Kazan       |
| 📍 Geocoding            | Yandex Maps API with support for Russian, Spanish, English, and Chinese |
| 🕊️ Reports              | Users can report areas with pigeons in real time                        |
| 🌍 Internationalization | Four languages: ES / EN / RU / 中文                                     |
| 📱 Responsive design    | Interface adapted for mobile and desktop devices                        |

---

## 🏗️ Architecture

```text
pigeonfree/
├── backend/                    # FastAPI + Python
│   ├── main.py                 # Main REST API
│   ├── data/                   # Datasets and ML models
│   │   ├── palomas_validadas_v2.json    # iNaturalist data validated with YOLO
│   │   ├── palomas_ebird.json           # eBird Tatarstan data
│   │   ├── palomas_ebird_historic.json  # Historical eBird data from 2023–2025
│   │   ├── palomas_con_clima.json       # eBird data + historical weather
│   │   ├── pseudoausencias.json         # Generated negative samples
│   │   ├── urban_features.json          # OpenStreetMap POIs
│   │   └── modelo_palomas_v5.pkl        # ML model v5
│   └── scripts/                # Data processing and training scripts
│       ├── download_inat.py             # Downloads iNaturalist data
│       ├── validate_yolo.py             # Validates images with YOLOv8
│       ├── download_ebird.py            # Downloads recent eBird data
│       ├── download_ebird_historic.py   # Downloads historical eBird data
│       ├── download_osm_features.py     # Downloads OSM points of interest
│       ├── add_weather_to_data.py       # Adds historical weather data
│       ├── generate_negatives.py        # Generates pseudo-absence samples
│       ├── train_model_v5.py            # Trains the final model
│       └── upload_to_supabase.py        # Uploads data to Supabase
├── frontend/                   # Next.js 16 + TypeScript
│   ├── app/
│   │   ├── components/
│   │   │   ├── Map.tsx                  # Leaflet map with ML risk zones
│   │   │   ├── SearchPanel.tsx          # Search and route calculation
│   │   │   ├── ReportButton.tsx         # User reporting interface
│   │   │   ├── SplashScreen.tsx         # Radar-style loading screen
│   │   │   ├── LanguageSwitcher.tsx     # Language selector
│   │   │   └── I18nProvider.tsx         # i18next provider
│   │   └── public/locales/              # ES/EN/RU/ZH translations
└── osrm/                       # Self-hosted OSRM server for Kazan
    └── kazan.osrm              # Kazan pedestrian routing data
```

---

## 🤖 Machine Learning Pipeline

### Training Data

| Source                           | Observations | Exact Time |
| -------------------------------- | ------------ | ---------- |
| iNaturalist, validated with YOLO | 357          | ❌         |
| eBird Tatarstan, last 30 days    | 57           | ✅         |
| Historical eBird data, 2023–2025 | 104          | ✅         |
| Generated pseudo-absences        | 1,036        | ✅         |
| **Total**                        | **1,554**    |            |

### Model Features

**Cyclical temporal features:**

- `hora_sin`, `hora_cos` — time of day represented as a 24-hour cycle
- `mes_sin`, `mes_cos` — month represented as a 12-month cycle
- `dia_semana` — day of the week
- `es_fin_de_semana` — whether the date falls on a weekend

**Real-time weather features:**

- Temperature
- Precipitation
- Wind speed
- Humidity
- `llueve` — binary rain indicator
- `nieva` — binary snow indicator

**Urban features**, calculated using four radii: 100 m, 300 m, 500 m, and 1 km:

- Restaurants, cafés, and fast-food locations
- Transport stations and bus stops
- Parks, squares, waste-disposal points, and markets

### Model v5 Metrics

| Metric              | Value                                              |
| ------------------- | -------------------------------------------------- |
| ROC-AUC, GroupKFold | **0.997**                                          |
| Brier Score         | **0.012**                                          |
| Log Loss            | —                                                  |
| Validation method   | GroupKFold using spatial grid groups               |
| Calibration         | Isotonic calibration with `CalibratedClassifierCV` |

### Most Important Features

```text
hora_cos:              13.9%
restaurantes_1000m:    13.3%
basura_1000m:          10.6%
parques_1000m:          8.1%
restaurantes_500m:      7.6%
hora_sin:               7.1%
estaciones_500m:        6.2%
estaciones_1000m:       6.1%
```

---

## 🛠️ Tech Stack

### Backend

- **FastAPI** — asynchronous REST API
- **Python 3.14**
- **scikit-learn** — Random Forest and isotonic calibration
- **YOLOv8 by Ultralytics** — pigeon detection in uploaded images
- **Supabase** — PostgreSQL database with PostGIS
- **Open-Meteo** — free real-time weather data
- **Yandex Geocoder API** — address geocoding for Russia

### Frontend

- **Next.js 16**, using the App Router
- **TypeScript**
- **Leaflet.js**
- **OpenStreetMap / CARTO**
- **i18next** — internationalization for ES, EN, RU, and ZH
- **Tailwind CSS**

### Infrastructure

- **OSRM** — self-hosted pedestrian routing server for Kazan
- **Docker** — OSRM containerization
- **Supabase** — cloud database

### Data Sources

- **iNaturalist API** — observations of _Columba livia_
- **eBird API** — Rock Pigeon observations in Tatarstan
- **OpenStreetMap Overpass API** — urban points of interest
- **Open-Meteo Historical API** — historical weather used to enrich observations

---

## 🚀 Local Installation

### Requirements

- Python 3.12 or later
- Node.js 18 or later
- Docker
- macOS or Linux

### Backend

```bash
# Clone the repository
git clone https://github.com/Marias03/pigeonfree.git
cd pigeonfree

# Create a virtual environment
python3 -m venv venv --without-pip
source venv/bin/activate
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py

# Install dependencies
pip install fastapi uvicorn httpx supabase python-dotenv \
            scikit-learn pandas numpy ultralytics pillow \
            openmeteo-requests requests-cache

# Configure environment variables
cp backend/.env.example backend/.env
# Edit backend/.env and add your API keys

# Start the backend
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### OSRM Pedestrian Routing

```bash
cd osrm

# Download the Kazan map
curl "https://overpass-api.de/api/map?bbox=48.8,55.6,49.5,56.1" -o kazan.osm

# Process the data with Docker
docker run -t -v "${PWD}:/data" ghcr.io/project-osrm/osrm-backend osrm-extract -p /opt/foot.lua /data/kazan.osm
docker run -t -v "${PWD}:/data" ghcr.io/project-osrm/osrm-backend osrm-partition /data/kazan.osrm
docker run -t -v "${PWD}:/data" ghcr.io/project-osrm/osrm-backend osrm-customize /data/kazan.osrm

# Start the routing server
docker run -d -p 5001:5000 -v "${PWD}:/data" ghcr.io/project-osrm/osrm-backend osrm-routed --algorithm mld /data/kazan.osrm
```

### Environment Variables

```env
# backend/.env
YANDEX_API_KEY=your_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
EBIRD_API_KEY=your_key_here
```

---

## 📡 API Endpoints

| Method | Endpoint                                 | Description                                          |
| ------ | ---------------------------------------- | ---------------------------------------------------- |
| `GET`  | `/geocode?q=текст&lang=en`               | Geocodes an address in Kazan                         |
| `GET`  | `/zones`                                 | Returns pigeon zones with ML-generated probabilities |
| `GET`  | `/route?from_lat&from_lng&to_lat&to_lng` | Calculates a walking route and analyzes pigeon risk  |
| `GET`  | `/predict?lat&lng`                       | Generates an ML prediction for a specific location   |
| `GET`  | `/weather`                               | Returns the current weather in Kazan                 |
| `POST` | `/report?lat&lng`                        | Submits a pigeon report for a location               |
| `GET`  | `/health`                                | Returns the server status                            |

---

---

## 🗺️ Map Features

- **ML-generated risk zones:** red above 60%, orange between 35% and 60%, and green below 35%
- **Dynamic circle size:** larger circles represent higher predicted probabilities
- **Informative popups:** probability, progress bar, and risk level
- **Pedestrian routes:** calculated using the self-hosted OSRM server
- **Route analysis:** calculates the average probability of encountering pigeons along the route
- **Community reporting:** users can mark areas where pigeons are present in real time

---

## 🌍 Internationalization

The application supports four languages and can automatically detect the browser language:

| Language | Code | Status |
| -------- | ---- | ------ |
| Spanish  | `es` | ✅     |
| English  | `en` | ✅     |
| Russian  | `ru` | ✅     |
| Chinese  | `zh` | ✅     |

---

---

## 🔜 Roadmap

- [ ] Deploy the frontend on Vercel and the backend on Railway
- [ ] Develop a mobile application using React Native and Expo
- [ ] Use Street View images and YOLO to detect additional pigeon-risk zones automatically
- [ ] Integrate the complete historical eBird EBD dataset
- [ ] Implement an A\* routing algorithm that penalizes street segments according to their predicted pigeon risk
- [ ] Add real-time alerts while the user is walking
- [ ] Validate user reports with YOLO before saving them

---

_PigeonFree — because walking should not be stressful._ 🕊️🚫
