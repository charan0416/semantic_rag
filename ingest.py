import os
from dotenv import load_dotenv
import pandas as pd
# from langchain.vectorstores import FAISS
# from langchain.embeddings import OpenAIEmbeddings
# from langchain.document_loaders import (TextLoader,CSVLoader,PyPDFLoader,Docx2txtLoader)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader, CSVLoader, PyPDFLoader, Docx2txtLoader,UnstructuredExcelLoader
from langchain_core.documents import Document

def load_selected_asset_csv(file_path, output_path=None):
    """
    Loads a CSV, keeps only 'AssetID' and 'EmpID', fills missing values with 'null',
    and sets EmpID to 'unassigned' if blank.
    Returns the filtered DataFrame (and optionally saves to output_path).
    """
    # Load CSV into DataFrame, convert all missing values to 'null'
    df = pd.read_csv(file_path, dtype=str).fillna("null")

    # Select only desired columns
    df = df[["AssetID", "EmpID"]]

    # Set EmpID to 'unassigned' if it is 'null'
    df.loc[:, "EmpID"] = df["EmpID"].apply(lambda x: "unassigned" if x == "null" else x)

    # Optionally save to output_path
    if output_path is not None:
        df.to_csv(output_path, index=False)

    return df



load_dotenv()
DOCS_PATH = "documents"

def get_all_documents(processed=None):
    docs = []
    processed_files = []
    for filename in os.listdir(DOCS_PATH):
        file_path = os.path.join(DOCS_PATH, filename)
        ext = os.path.splitext(filename)[1].lower()
        if filename in processed_files:
            continue
        try:
            if ext == ".txt":
                loader = TextLoader(file_path, encoding="utf-8")
            elif ext == ".csv":
                if filename == "Asset History.csv":
                    # Define paths
                    process_file = f"filtered_{filename}"
                    filtered_path = os.path.join(DOCS_PATH, process_file)
                    # Save filtered CSV
                    processed_files.append(process_file)
                    filtered_df = load_selected_asset_csv(file_path, filtered_path)
                    # Use new filtered file with CSVLoader
                    loader = CSVLoader(filtered_path)
                else:
                    loader = CSVLoader(file_path)

            elif ext == ".pdf":
                loader = PyPDFLoader(file_path)
            elif ext == ".docx":
                loader = Docx2txtLoader(file_path)
            elif ext in [".xlsx", ".xls"]:
                # Prefer UnstructuredExcelLoader for general purposes
                loader = UnstructuredExcelLoader(file_path)
            else:
                print(f"⚠️ Unsupported file format: {filename}")
                continue

            file_docs = loader.load()
            docs.extend(file_docs)
            print(f"✅ Loaded: {filename} ({len(file_docs)} chunks)")
        except Exception as e:
            print(f"❌ Failed to load {filename}: {e}")

    return docs


def ingest_docs():
    print("📥 Starting document ingestion...")
    raw_docs = get_all_documents()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.split_documents(raw_docs)

    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(docs, embeddings)

    db.save_local("vector_store")
    print("✅ Ingestion complete and FAISS DB saved.")

if __name__ == "__main__":
    ingest_docs()