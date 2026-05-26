# 🌌 FAISS Visualizer: 3D Latent Space Visualization Suite
## aka FAISS Viewer

Ever wondered what your RAG (Retrieval-Augmented Generation) document chunks actually look like in the latent space? FAISSViewer is a suite of tools designed to extract, project, and visualize LangChain FAISS vector databases in interactive 3D environments.

Whether you want a quick web plot to map new queries against your data, or you want to literally fly through your database in a 3D game engine, this suite has you covered!

## 🧰 What's Inside?

This project consists of three main components:

### 1. The Exporter (`exportFaissEmbeds.py`)

A Python script that safely loads a LangChain FAISS index and exports it to a portable JSON format.

* **Extracts Everything:** Can pull document text, metadata, and the raw high-dimensional embeddings straight from the database.
* **Dimensionality Reduction:** Uses `umap-learn` to crunch dense vectors (e.g., 768d or 1536d) down into 3D coordinates (X, Y, Z) so humans can actually comprehend them.
* **Highly Customizable:** Features flags like `--save-min`, `--save-default`, and `--save-all` to give you complete control over file size and data privacy.

### 2. Plotly Web Visualizers

We provide two Python-based browser visualizers depending on your needs:

* **`WebVisualiserS.py` (Simple):** A lightweight script that reads your exported JSON and immediately spins up an interactive 3D Plotly scatter plot. It automatically truncates text for clean hover-states and applies a visually pleasing dark theme.
* **`WebVisualiser.py` (Advanced):** Takes things to the next level. Not only does it plot your database, but it also allows you to embed *new* user queries on the fly and project them into the exact same 3D space.
* Supports mapping queries via local models (Ollama, HuggingFace) or external APIs (OpenAI/Proxies).
* Load batch queries from a CSV or type them interactively in the terminal.
* Visually compares your standard "Database Documents" (blue dots) against your new "User Queries" (orange diamonds).



### 3. Godot Engine 3D Renderer

Want to physically explore your data? We built a Godot project that renders your dataset as an immersive 3D world.

* **High Performance:** Uses `MultiMeshInstance3D` and a custom shader to render thousands of data points smoothly without melting your GPU.
* **Dynamic Styling:** Data blocks are automatically colored based on their spatial position, featuring a clean procedural outline shader. You can even dynamically resize the cubes using your mouse wheel.
* **Fly Camera:** Jump in and use standard `WASD` + `QE` controls to fly around your dataset.
* **Interactive Raycasting:** Look directly at any floating data point and hit `ENTER` or `TAB` to pop open an in-game UI displaying the text chunk and its associated metadata.

---

## 🚀 Getting Started

### Prerequisites

* **Python 3.8+**
* Required Python packages: `langchain-community`, `langchain-openai`, `faiss-cpu`, `umap-learn`, `pandas`, `plotly`
* **Godot Engine 4.x** (for the 3D renderer)

### Step 1: Export your FAISS Database

Point the exporter to your folder containing `index.faiss` and `index.pkl`.

```bash
python exportFaissEmbeds.py ./path_to_your_faiss_folder output.json --save-all

```

### Step 2: Visualize in the Browser

If you just want a fast 3D view of the shape of your data:

```bash
python WebVisualiserS.py output.json

```

If you want to map new queries (e.g., using a local Ollama model to see which documents your query lands near):

```bash
python WebVisualiser.py output.json "nomic-embed-text" "http://localhost:11434"

```

### Step 3: Explore in Godot

1. Open the `FaissViewer/GodotRenderer` folder in Godot 4.
2. Hit **Play** (F5).
3. A file dialog will appear centrally on your screen. Select your generated `output.json`.
4. **Controls:**
* `Mouse`: Look around
* `W/A/S/D`: Move horizontally
* `Q/E`: Move down / up
* `Mouse Wheel`: Scale the data cubes up or down
* `ENTER` or `TAB`: Inspect the text and metadata of the data block you are currently looking at
* `ESC`: Free your mouse cursor



## 💡 Why build this?

Vector databases can feel like a total "black box". By visualizing your chunks in 3D, you can easily spot anomalies, see how well your embedding model groups related topics, and debug why specific RAG queries are failing by seeing exactly where your query lands in relation to your knowledge base.

Enjoy exploring your latent spaces! 🚀