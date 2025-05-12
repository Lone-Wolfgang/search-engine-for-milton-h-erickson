## DocuTrance: Indexing and Retrieval for a Private Collection of Documents

This is a package for launching a search engine for browsing the *Collected Works of Milton H. Erickson*. It is built on OpenSearch and uses a hybrid approach combining keyword and semantic scoring, aligning with the funcionalities of modern search interfaces. While Erickson's works are in English, he has a huge audience in Europe and East Asia. The semantic model used for retrieval is multilingual, relatively lightweight, and surprisingly performant.

A personal document retrieval system is a practical tool for anyone managing a lot of documents. This codebase is intended as a starting point for others to adapt. Some components—such as text extraction and document indexing—are  hardcoded for this collection. Others, like the search query logic, are designed to be more modular. Over time, this project may evolve to support broader use cases with improved generalization.

## Software Stack and Hardware Requirements

### Software Stack

- **Operating System**: Developed and tested on Windows 10
- **Search Engine**: OpenSearch (deployed via Docker)
- **Backend**: Python
- **Frontend**: Streamlit
- **NLP**: spaCy (used for lemmatization and preprocessing)

### Hardware Requirements

- **Minimum**
  - CPU: Dual-core processor (2.0 GHz or higher)
  - RAM: 8 GB
  - Storage: 5 GB free space
  - Docker Desktop installed and running

## Installation

OpenSearch is deployed using Docker, which simplifies setup and avoids the need for a full manual install. This approach was used during development on a Windows machine and proved to be straightforward.

To install Docker, follow the official guide:  
[https://docs.docker.com/get-started/get-docker/](https://docs.docker.com/get-started/get-docker/)

Once Docker is installed and running, you can clone the repository and set up your Python environment. This project was developed using Python 3.10 and has not been tested with other versions.

```bash
#Setup a virtual environemnt with Python 3.10

# Clone the repository
git clone https://github.com/Lone-Wolfgang/DocuTrance.git
cd DocuTrance


# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Setting Up OpenSearch with Docker

OpenSearch is installed using Docker Compose. The provided `docker-compose.yml` installs **OpenSearch 2.13**, which includes semantic search capabilities and support for advanced filtering. It also installs **OpenSearch Dashboards**, allowing you to browse and inspect your index via a web UI.

The only required configuration in the `docker-compose.yml` file is the **password**. If you plan to run multiple nodes, you will also need to configure the **node name** and adjust the **port values** accordingly.

### Start OpenSearch

From the project root, run the following script to bring up the search engine:

```bash
# Set your password in docker-compose.yml before running this
cd docker
docker compose up -d
```
Wait a few minutes for the containers to fully initialize.
If you're using the default settings, you can access OpenSearch Dashboards at:

http://localhost:5601/app/home#/

## Deploying the Semantic Search Model

The final setup step is to deploy the model used for semantic search. OpenSearch provides access to several pretrained models with varying language coverage and performance characteristics.

For this project, the selected model is:

**`huggingface/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`**

This is a lightweight multilingual model that balances efficiency with relevance and supports a global user base.

To deploy the model, follow the official OpenSearch documentation:  
[https://docs.opensearch.org/docs/latest/ml-commons-plugin/pretrained-models/](https://docs.opensearch.org/docs/latest/ml-commons-plugin/pretrained-models/)

After successful deployment, OpenSearch will return a `model_id`.  
Save this `model_id` to your `config.py` file.

Once the model ID is configured, the semantic search pipeline is staged and ready to use.

## Indexing Your Documents

The indexing script provided in this project is currently hardcoded for the documents used during development. If you are building your own search engine with a different document set or structure, you will need to modify the script accordingly.

The following fields are extracted during indexing:

**Content:**
- `title`
- `headers`
- `body`

**Metadata:**
- `order`
- `author`
- `volume`
- `section`
- `chapter`

The indexing pipeline generates embeddings for the `title`, `headers`, and `body`. These embeddings power the semantic search functionality. The model used is optimized for clustering multilingual sentences and short paragraphs. 

### Run the Indexing Script

After configuring your index and ensuring your documents are in the expected format, run the following:

```bash
python ingest.py
```
If your documents were properly indexed, you can browse and verify them in OpenSearch Dashboards:
http://localhost:5601/app/home#/

### Launching the App

Once your documents are indexed and the model is deployed, you can launch the search interface.

If you changed the configuration of the index, you will also need to update the relevant modules in `ux.py` to match your index structure.

To start the app:

```bash
streamlit run app.py
```
Additional settings—such as the search algorithm, display layout, and model ID—can be configured in config.py.

If you encounter issues or unexpected results, set DEBUG=True in config.py to view the search queries as they are dynamically generated. This can assist with troubleshooting.





