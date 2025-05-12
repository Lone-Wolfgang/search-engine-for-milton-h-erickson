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

