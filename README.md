# 🎓 AI Fellowship Assignments

This repository contains all my assignments, projects, and practical implementations completed during the **AI Fellowship** program.

---

## 📚 Curriculum & Completed Modules

| Week | Folder | Topic | Description |
| :---: | :--- | :--- | :--- |
| 1 | [`week1_data_wrangling_and_sql`](./week1_data_wrangling_and_sql) | **Data Wrangling & SQL** | Python data manipulation, Pandas, and SQL queries. |
| 2 | [`week2_rest_api_development`](./week2_rest_api_development) | **REST API Development** | Full REST API over a sales database with FastAPI, Docker, and layered architecture. |
| 3 | [`week3_text_to_sql_agent`](./week3_text_to_sql_agent) | **Text-to-SQL Agent** | LLM-powered agent that decomposes natural language into SQL queries. |
| 4 | [`week4_linear_models`](./week4_linear_models) | **Linear Models** | Linear regression, logistic regression, and regularization techniques. |
| 5 | [`week5_tree_based_models_and_ensembles`](./week5_tree_based_models_and_ensembles) | **Tree-Based Models & Ensembles** | Decision trees, random forests, gradient boosting, and XGBoost. |
| 6 | [`week6_probabilistic_models`](./week6_probabilistic_models) | **Probabilistic Models** | Bayesian methods and probabilistic reasoning. |
| 7 | [`week7_clustering`](./week7_clustering) | **Clustering** | K-Means, hierarchical clustering, and cluster evaluation. |
| 8 | [`week8_forecasting`](./week8_forecasting) | **Forecasting** | Time series analysis, SARIMA, and forecasting techniques. |
| 9 | [`week9_deep_learning_defect_detection`](./week9_deep_learning_defect_detection) | **Deep Learning & Defect Detection** | CNN-based steel surface defect classification (SmartForge). |
| 10 | [`week10_computer_vision_opencv`](./week10_computer_vision_opencv) | **Computer Vision with OpenCV** | Image processing and automated fruit sorting (FreshTrack). |
| 11 | [`week11_computer_vision_deep_learning`](./week11_computer_vision_deep_learning) | **Computer Vision with Deep Learning** | Deep learning for image classification on CIFAR-10. |
| 12 | [`week12_named_entity_recognition`](./week12_named_entity_recognition) | **Named Entity Recognition (NER)** | End-to-end NER pipeline for customer support ticket analysis. |
| 13 | [`week13_lstm_text_classification`](./week13_lstm_text_classification) | **LSTMs for Text Classification** | LSTM networks for AG_NEWS topic classification. |
| 14 | [`week14_agentic_routing_with_llms`](./week14_agentic_routing_with_llms) | **Agentic Routing with LLMs & Transformers** | LLM-powered support ticket routing (ShopAssist AI). |
| 15 | [`week15_enterprise_ai_assistant`](./week15_enterprise_ai_assistant) | **Enterprise AI Assistant** | RAG with ChromaDB, semantic search, and production AI engineering. |
| 16 | [`week16_autonomous_agentic_ai`](./week16_autonomous_agentic_ai) | **Autonomous Agentic AI & Evaluation** | Multi-step ReAct agent loop, tool calling, verifier agents, and evaluation suites. |
| 17 | [`week17_mlops_pipelines`](./week17_mlops_pipelines) | **MLOps Pipelines & Drift Monitoring** | End-to-end MLOps: MLflow tracking, Evidently AI drift monitoring, FastAPI serving, and Airflow DAGs. |
| 18 | [`week18_trustworthy_ai_guardrails`](./week18_trustworthy_ai_guardrails) | **Trustworthy AI Guardrails** | Defense-in-depth input & output guardrail system for LLM applications. |

---

## 🛠️ Technologies & Tools Used

* **Languages & Core**: Python 3.10+, NumPy, Pandas, Scikit-learn
* **Deep Learning & NLP**: PyTorch, Hugging Face Transformers, Sentence-Transformers, LSTMs, CNNs
* **Computer Vision**: OpenCV, torchvision
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

# Go to any specific week (e.g. week17_mlops_pipelines)
cd week17_mlops_pipelines/track_a
uv sync
uv run python src/train.py
```

---

## 👤 Contributors
* **Roja Shrestha** — [@rojashrestha](https://github.com/rojashrestha)
* **Contributor** — [@rojasthaa](https://github.com/rojasthaa)
