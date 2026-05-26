import argparse
import json
import os
import sys
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

# --- Dummy Class to bypass model loading ---
class DummyEmbeddings(Embeddings):
    def embed_documents(self, texts): return []
    def embed_query(self, text): return []

def export_faiss_to_json(input_folder, output_file, allow_dangerous, save_text, save_metadata, save_embeddings, save_3d):
    # 1. Validation
    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist.")
        sys.exit(1)

    print(f"--- Loading FAISS index from: {input_folder} ---")
    
    try:
        # 2. Load the Vector Store without a model
        vector_store = FAISS.load_local(
            folder_path=input_folder, 
            embeddings=DummyEmbeddings(), 
            allow_dangerous_deserialization=allow_dangerous
        )

        faiss_index = vector_store.index
        docstore = vector_store.docstore._dict
        id_mapping = vector_store.index_to_docstore_id
        
        total = faiss_index.ntotal
        print(f"--- Found {total} records. Extracting data... ---")

        # 3. Handle UMAP 3D Projection (Only if requested)
        umap_embeddings = None
        if save_3d:
            print("--- Calculating 3D UMAP projection (this may take a moment)... ---")
            try:
                import umap
            except ImportError:
                print("Error: 'umap-learn' is not installed. Please run 'pip install umap-learn' to use the 3D feature.")
                sys.exit(1)
            
            # Extract all vectors efficiently for the math engine
            all_vectors = np.array([faiss_index.reconstruct(i) for i in range(total)])
            
            # Compress to 3 dimensions
            reducer = umap.UMAP(n_components=3, random_state=42)
            umap_embeddings = reducer.fit_transform(all_vectors)
            print("--- 3D projection complete. ---")

        output_data = []

        # 4. Iterate and build the JSON structure
        for i in range(total):
            doc_id = id_mapping[i]
            doc = docstore[doc_id]
            
            record = {"id": doc_id}
            
            if save_text:
                record["text"] = doc.page_content
            if save_metadata:
                record["metadata"] = doc.metadata
            if save_embeddings:
                record["embedding"] = faiss_index.reconstruct(i).tolist()
            if save_3d:
                # Convert the NumPy array slice back to a standard Python list for JSON serialization
                record["position_3d"] = umap_embeddings[i].tolist()
                
            output_data.append(record)

        # 5. Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        
        print(f"--- Success! Exported to: {output_file} ---")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export LangChain FAISS index to JSON with selective data components.")
    
    # Core requirements
    parser.add_argument("input_folder", help="Path to the folder containing index.faiss and index.pkl")
    parser.add_argument("output_json", help="Path for the output JSON file")
    
    # Data inclusion flags
    parser.add_argument("--save-text", action="store_true", help="Include document text in the output")
    parser.add_argument("--save-metadata", action="store_true", help="Include document metadata in the output")
    parser.add_argument("--save-embeddings", action="store_true", help="Include original high-dimensional embeddings")
    parser.add_argument("--save-3d", action="store_true", help="Calculate and include 3D UMAP coordinates")
    parser.add_argument("--save-all", action="store_true", help="Include text, metadata, embeddings, AND 3D coordinates")
    parser.add_argument("--save-default", action="store_true", help="Include text, metadata and 3D coordinates")
    parser.add_argument("--save-min", action="store_true", help="Include text and 3D coordinates")
    
    # Security flag
    parser.add_argument(
        "--disallow_dangerous", 
        dest="allow_dangerous", 
        action="store_false",
        help="Disable dangerous deserialization (default is enabled)"
    )
    parser.set_defaults(allow_dangerous=True)

    args = parser.parse_args()

    # Logic to handle the "--save-all" override
    if args.save_all:
        args.save_text = True
        args.save_metadata = True
        args.save_embeddings = True
        args.save_3d = True
        
    if args.save_min:
        args.save_text = True
        args.save_metadata = False
        args.save_embeddings = False
        args.save_3d = True
        
    if args.save_default:
        args.save_text = True
        args.save_metadata = True
        args.save_embeddings = False
        args.save_3d = True

    # Fallback default: If the user provided no specific save flags, default to text and embeddings
    if not any([args.save_text, args.save_metadata, args.save_embeddings, args.save_3d, args.save_all]):
        print("No specific save arguments provided. Defaulting to saving text, metadata and 3D positions.")
        args.save_text = True
        args.save_metadata = True
        args.save_embeddings = False
        args.save_3d = True

    # Execute
    export_faiss_to_json(
        input_folder=args.input_folder, 
        output_file=args.output_json, 
        allow_dangerous=args.allow_dangerous,
        save_text=args.save_text,
        save_metadata=args.save_metadata,
        save_embeddings=args.save_embeddings,
        save_3d=args.save_3d
    )
