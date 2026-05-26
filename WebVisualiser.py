import json
import pandas as pd
import plotly.express as px
import argparse
import numpy as np
import os
import textwrap

def run_visualizer(json_file_path, model_name, endpoint=None, api_key=None, csv_file=None, csv_sep=','):
    print(f"--- Opening {json_file_path} ---")
    
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    # 1. Prepare data containers
    records = []
    original_embeddings = []

    for entry in data:
        pos = entry.get("position_3d")
        if not pos or len(pos) < 3:
            continue
            
        full_text = entry.get("text", "No text provided")
        display_text = "<br>".join(textwrap.wrap(full_text, width=80))

        row = {
            "x": pos[0], "y": pos[1], "z": pos[2],
            "text": display_text,
            "id": entry.get("id", "N/A"),
            "type": "Database Document" 
        }
        
        metadata = entry.get("metadata", {})
        if isinstance(metadata, dict):
            for key, val in metadata.items():
                row[f"meta_{key}"] = str(val)

        records.append(row)
        if "embedding" in entry:
            original_embeddings.append(entry["embedding"])

    if not records:
        print("Error: No valid records found.")
        return

    df = pd.DataFrame(records)
    print(f"--- Loaded {len(df)} points from database ---")

    # 2. Gather Prompts to Embed
    prompts_to_embed = []

    # 2a. Load from CSV if provided
    if csv_file:
        if os.path.exists(csv_file):
            try:
                csv_df = pd.read_csv(csv_file, sep=csv_sep)
                # Auto-detect column name
                col_to_use = None
                for col in ['prompt', 'text', 'query']:
                    if col in csv_df.columns:
                        col_to_use = col
                        break
                if not col_to_use:
                    col_to_use = csv_df.columns[0] # Fallback to first column
                
                loaded_prompts = csv_df[col_to_use].dropna().astype(str).tolist()
                prompts_to_embed.extend(loaded_prompts)
                print(f"--- Loaded {len(loaded_prompts)} prompts from CSV (column: '{col_to_use}') ---")
            except Exception as e:
                print(f"Error reading CSV: {e}")
        else:
            print(f"CSV file not found: {csv_file}")

    # 2b. Gather Interactive Prompts
    print("\nEnter prompts to visualize (Type your prompt and press Enter).")
    print("Press Enter on an empty line when you are finished:")
    while True:
        p = input("> ").strip()
        if not p:
            break
        prompts_to_embed.append(p)
    
    # 3. Map Prompts to Latent Space
    if prompts_to_embed:
        if not original_embeddings:
            print("\n⚠️ ERROR: You must export with --save-embeddings to map new prompts.")
        else:
            try:
                # --- EMBEDDING MODEL ROUTING LOGIC ---
                if endpoint and ("11434" in endpoint or "ollama" in endpoint.lower()):
                    print(f"\nUsing Ollama API | Model: {model_name} | Endpoint: {endpoint}")
                    from langchain_community.embeddings import OllamaEmbeddings
                    embedding_model = OllamaEmbeddings(base_url=endpoint, model=model_name)
                    
                elif endpoint or "text-embedding" in model_name.lower() or "gpt" in model_name.lower():
                    provider = "OpenAI API" if not endpoint else "OpenAI-Compatible Proxy"
                    print(f"\nUsing {provider} | Model: {model_name}")
                    from langchain_openai import OpenAIEmbeddings
                    
                    openai_kwargs = {"model": model_name}
                    if endpoint:
                        openai_kwargs["openai_api_base"] = endpoint
                    if api_key:
                        openai_kwargs["openai_api_key"] = api_key
                    elif not os.environ.get("OPENAI_API_KEY"):
                        openai_kwargs["openai_api_key"] = "dummy-key"
                        
                    embedding_model = OpenAIEmbeddings(**openai_kwargs)
                    
                else:
                    print(f"\nUsing HuggingFace local model: {model_name}...")
                    from langchain_community.embeddings import HuggingFaceEmbeddings
                    embedding_model = HuggingFaceEmbeddings(model_name=model_name)
                
                # --- EMBEDDING & PROJECTION ---
                print(f"\nEmbedding {len(prompts_to_embed)} prompts...")
                # embed_documents takes a list and is much faster for batch processing
                prompt_embeddings = embedding_model.embed_documents(prompts_to_embed)
                
                print("Calculating UMAP projection (using seed 42)...")
                import umap
                reducer = umap.UMAP(n_components=3, random_state=42)
                reducer.fit(np.array(original_embeddings))
                
                # Transform the entire batch of prompts at once
                prompts_3d = reducer.transform(np.array(prompt_embeddings))
                
                # Add all prompts to the dataframe
                prompt_rows = []
                for i, p_3d in enumerate(prompts_3d):
                    prompt_rows.append({
                        "x": p_3d[0], "y": p_3d[1], "z": p_3d[2],
                        "text": f"PROMPT: {prompts_to_embed[i]}", 
                        "id": f"USER_QUERY_{i+1}", 
                        "type": "User Query"
                    })
                
                df = pd.concat([df, pd.DataFrame(prompt_rows)], ignore_index=True)
                print("--- Success! Mapped all prompts into the 3D space. ---")
                
            except ImportError as e:
                print(f"\nMissing required library: {e}")
                print("Ensure you have installed: langchain-openai langchain-community sentence-transformers umap-learn pandas")
            except Exception as e:
                print(f"\nAn error occurred while embedding/mapping: {e}")

    # 4. Build & Show Plot
    fig = px.scatter_3d(
        df, x="x", y="y", z="z", color="type",
        color_discrete_map={"Database Document": "#1f77b4", "User Query": "#ff7f0e"},
        hover_name="id", hover_data={"text": True, "x": False, "y": False, "z": False, "type": False},
        title=f"FAISS 3D Visualizer | Model: {model_name}",
        opacity=0.8, template="plotly_dark"
    )

    # Make standard database points tiny
    fig.update_traces(marker=dict(size=3, line=dict(width=0)), selector=dict(name="Database Document"))
    
    # Make User Queries distinct but smaller than before (size 6 instead of 12)
    fig.update_traces(marker=dict(size=6, symbol="diamond", line=dict(width=1, color="white")), selector=dict(name="User Query"))
    
    fig.update_layout(margin=dict(l=0, r=0, b=0, t=40), scene=dict(xaxis_title='UMAP 1', yaxis_title='UMAP 2', zaxis_title='UMAP 3'))
    fig.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize FAISS latent space and map new prompts.")
    parser.add_argument("json_file", help="Path to the exported JSON file")
    parser.add_argument("model_name", help="Name of the embedding model")
    parser.add_argument("endpoint", nargs='?', default=None, help="(Optional) API endpoint URL")
    parser.add_argument("api_key", nargs='?', default=None, help="(Optional) API Key")
    
    # New CSV arguments
    parser.add_argument("--csv", dest="csv_file", default=None, help="Path to a CSV file containing multiple prompts")
    parser.add_argument("--sep", dest="csv_sep", default=",", help="Separator for the CSV file (default: ',')")
    
    args = parser.parse_args()
    
    run_visualizer(args.json_file, args.model_name, args.endpoint, args.api_key, args.csv_file, args.csv_sep)