# 🎓 AI Fellowship Assignments

This repository contains all my assignments, projects, and practical implementations completed during the **AI Fellowship** program.

---

## 📚 Curriculum & Completed Modules.

| Folder | Topic / Module | Description |
| :--- | :--- | :--- |
| [`week1_task`](./week1_task) | **Foundations & Environment** | Python setup, data manipulation, and programming foundations. |
| [`week2`](./week2) – [`week9`](./week9) | **Machine Learning & Deep Learning** | Supervised & unsupervised learning, classification, regression, neural network architectures, and model evaluations. |
| [`week15`](./week15) | **RAG & Vector Databases** | Semantic search using ChromaDB, dense embeddings, and document retrieval. |
| [`week16`](./week16) | **Agentic AI & Evaluation** | Multi-step ReAct agent loop, tool calling, verifier agents, and benchmark evaluation suites. |
| [`week17`](./week17) | **MLOps & Drift Monitoring** | End-to-end MLOps: Experiment tracking (MLflow), data/target drift monitoring (Evidently AI), model serving (FastAPI), and Airflow orchestration DAGs. |
| [`week18`](./week18) | **Advanced Systems** | Scaling, deployment, and practical AI systems. |

---

## 🛠️ Technologies & Tools Used

* **Languages & Core**: Python 3.10+, NumPy, Pandas, Scikit-learn
* **Deep Learning & NLP**: PyTorch, Hugging Face Transformers, Sentence-Transformers
* **Vector Stores & RAG**: ChromaDB
* **Agentic Frameworks & APIs**: FastAPI, Streamlit, REST APIs
* **MLOps & DevOps**: MLflow, Evidently AI, Apache Airflow, Docker, `uv`

---

## 🚀 How to Run Any Assignment

Most modules use standard Python or `uv` for reproducible environments:

```bash
# Clone the repository
git clone https://github.com/rojashrestha/ai_fellowship_assignments.git
cd ai_fellowship_assignments

# Go to any specific week (e.g. week17)
cd week17/track_a
uv sync
uv run python src/train.py

* **Contributor**: [@rojasthaa](https://github.com/rojasthaa)


