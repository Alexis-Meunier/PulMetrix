# Software Architecture

Our PulMetrix application follows the principles of **layered architecture**.

## Overview of the Layers

The source code (`src/`) is divided into three main layers:

* **`presentation/`:**
    * Contains the REST controllers (`rest/`) that receive HTTP requests and return JSON responses (defined in `api/response/`).
* **`domain/` (Scientific Core):**
    * Contains entities (`entity/`) and image processing algorithms (*TVAC, Region Growing, metric calculation*).
* **`data/`  :**
    * Manages data persistence.
    * Uses the *Repository* pattern to communicate with the SQLite database via SQLModel.