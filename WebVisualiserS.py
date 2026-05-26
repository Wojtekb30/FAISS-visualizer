import json
import pandas as pd
import plotly.express as px
import sys

def run_visualizer(json_file_path):
    print(f"--- Opening {json_file_path} ---")
    
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    # 1. Prepare data containers
    records = []

    for entry in data:
        # Essential check: Does this entry have the 3D coordinates?
        pos = entry.get("position_3d")
        if not pos or len(pos) < 3:
            continue
            
        # Truncate text for hover readability
        full_text = entry.get("text", "No text provided")
        display_text = (full_text[:100] + '...') if len(full_text) > 100 else full_text

        # Create a row for the DataFrame
        row = {
            "x": pos[0],
            "y": pos[1],
            "z": pos[2],
            "text": display_text,
            "id": entry.get("id", "N/A")
        }
        
        # Flatten metadata into the row if it exists (allows coloring by metadata keys later)
        metadata = entry.get("metadata", {})
        if isinstance(metadata, dict):
            for key, val in metadata.items():
                row[f"meta_{key}"] = str(val)

        records.append(row)

    if not records:
        print("Error: No valid records with 'position_3d' found in the JSON.")
        return

    df = pd.DataFrame(records)
    print(f"--- Visualizing {len(df)} points ---")

    # 2. Build the Interactive Plot
    fig = px.scatter_3d(
        df, 
        x="x", y="y", z="z",
        hover_name="id",
        hover_data={"text": True, "x": False, "y": False, "z": False},
        title="FAISS Export: 3D Latent Space Visualization",
        opacity=0.8,
        template="plotly_dark"
    )

    # 3. Visual Styling
    fig.update_traces(
        marker=dict(
            size=3,
            line=dict(width=0),
            colorscale='Viridis'
        )
    )

    # Adjusting the layout to be more immersive
    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=40),
        scene=dict(
            xaxis_title='UMAP 1',
            yaxis_title='UMAP 2',
            zaxis_title='UMAP 3'
        )
    )

    fig.show()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_visualizer(sys.argv[1])
    else:
        example = '''[
    {
        "id": "57**d6",
        "text": "Sample text",
        "position_3d": [
            7.278976917266846,
            3.0890214443206787,
            -4.38466739654541
        ]
    },
    ...
    '''
        print("Please provide path to JSON as 1st argument. Minimal JSON example:\n"+example)