# PulMetrix

PulMetrix is a medical imaging application designed for lung segmentation and asymmetry analysis on DICOM-format chest X-rays.

The application incorporates two segmentation methods: an automatic approach using the TVAC (Total Variation-based Active Contour) algorithm and a semi-manual approach involving the selection of points of interest (Region Growing).

## Installation

### Option 1: Deployment with Docker (Recommended)

To run the entire application (frontend + backend API) without installing any local dependencies, use Docker Compose:

```bash
docker compose up -d
```

The interface will then be accessible on port 80 and the API on port 8000 (localhost in both cases).

### Option 2: Local Installation

This project uses the uv package manager. First, install uv, then sync the virtual environment. For the frontend, you need to install Node.js and npm.

- Clone the repository

```bash
git clone https://cri.epita.fr/lucil.finkelstein/pulmetrix.git
cd pulmetrix/backend
```

- Sync and install the dependencies listed in pyproject.toml

```bash
uv sync
```

## Usage

If you chose the local installation option:

- Start the backend server

From the backend folder: 

```bash
uv run fastapi run
```

- Start the frontend server

From the frontend folder:

```bash
npm run dev
```

If you chose the Docker installation option, once the containers have started, you can simply access the [interface](http://localhost:80).


You can interact with the API using the frontend, curl, or the interactive Swagger.