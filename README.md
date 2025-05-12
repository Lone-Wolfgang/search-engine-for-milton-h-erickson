## DocuTrance: Indexing and Retrieval for a Private Collection of Documents

This is a package for launching a search engine for browsing the *Collected Works of Milton H. Erickson*. It is built on OpenSearch and uses a hybrid approach combining keyword and semantic scoring, aligning with expectations set by modern search interfaces. While Erickson's works are in English, he has a significant audience in Europe and East Asia. The semantic model used for retrieval is multilingual and relatively lightweight. Given its constraints, performance is surprising.

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

Once Docker is installed and running, 
