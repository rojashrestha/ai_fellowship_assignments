# Steel Surface Defect Classification - Deep Learning Project
### AI Fellowship Week 9: SmartForge Manufacturing ML Assignment

This repository contains the complete implementation and theoretical analysis for classifying surface defects on hot-rolled steel strips using Deep Convolutional Neural Networks (CNNs). The model is trained on the standard NEU Steel Surface Defect Database to identify six types of physical manufacturing anomalies.

---

## 🚀 Key Project Features

### 1. Neural Network Foundations (Part 0)
- **Activation Functions**: Comparative analysis of **ReLU vs. Sigmoid** demonstrating how ReLU prevents the Vanishing Gradient Problem.
- **Loss Functions**: Analytical comparison of **Cross-Entropy vs. Mean Squared Error (MSE)** for classification tasks.
- **Optimizers**: Convergence rate comparison of **SGD, SGD with Momentum, and Adam** using fixed learning rates ($lr = 0.01$).
- **Regularization**: Stability analysis comparing **Batch Normalization** and **Dropout** in training vs. inference modes.

### 2. Defect Type Classifier (Part A)
- **Architecture**: A baseline 2-layer Convolutional Neural Network (CNN) designed to extract spatial features from $200 \times 200$ grayscale steel images.
- **Data Leakage Prevention**: Splitting the raw data into **80% Train, 10% Val, and 10% Test** partitions *before* applying image transformations using a custom PyTorch `DatasetWrapper` class.
- **Per-Class Metrics**: Evaluation using a classification report (F1-score, Precision, Recall) and confusion matrix.
- **Test Predictions Visualizer**: A custom plotting function that renders test batch predictions displaying `True Label` vs `Predicted Label` side-by-side with color-coded classification status (Green for Correct, Red for Incorrect).

### 3. Model Hardening (Part B)
- **Data Augmentation**: Training-only geometric augmentations (random horizontal flips, random rotations up to $15^\circ$, and random crops) to enforce translation and rotation invariance.
- **Regularization Layers**: Implementing `BatchNorm2d` after each Conv layer and `Dropout(0.4)` before the final linear projection layer to minimize overfitting.

### 4. Hyperparameter Tuning (Part C)
- **Grid Search**: Evaluating learning rates ($0.001$, $0.01$) against batch sizes ($16$, $32$).
- **Learning Rate Schedule**: Annealing step updates using `StepLR` (decaying learning rate by a factor of 0.5 every 5 epochs) to allow the optimizer to settle into deep local minima.
- **Bayesian Optimization**: Automated parameter space tuning (learning rate and batch size) using **Optuna**.

---

## 📂 Repository Structure

- 📁 `plots/` — Saved loss curves, stability plots, and final configuration comparison graphs.
- 📄 `SmartForge_Defect_Detection.ipynb` — The primary Jupyter Notebook, optimized and pre-configured for Google Colab (T4 GPU).
- 📄 `SmartForge_ML_Assignment_Reflection.pdf` — A formal, academic-style reflection report detailing findings on model hardening, vanishing gradients, optimizer memory footprints, and class confusions.
- 📄 `study_guide_roman_nepali.md` — A comprehensive study guide written in Roman Nepali for exam preparation and conceptual review.
- 📄 `README.md` — Documentation of the project workflow and structure.

---

## 📊 Dataset: NEU Surface Defect Database
The dataset contains 1,800 grayscale images representing six distinct surface defects of hot-rolled steel sheets:
1. **Crazing (Cr)** — Fine web-like cracks on the surface.
2. **Inclusion (In)** — Foreign materials pressed into the metal.
3. **Patches (Pa)** — Regional discoloration or texture changes.
4. **Pitted Surface (Ps)** — Small indentations or cavities.
5. **Rolled-in Scale (Rs)** — Oxide scale pressed into the strip during rolling.
6. **Scratches (Sc)** — Linear grooves caused by mechanical friction.

---

## ⚙️ Installation and Setup

### Google Colab (Recommended)
1. Open [Google Colab](https://colab.research.google.com/).
2. Click **File** -> **Upload notebook** and upload `SmartForge_Defect_Detection.ipynb`.
3. Go to **Runtime** -> **Change runtime type** -> select **T4 GPU** -> **Save**.
4. Drag and drop `archive (4).zip` (the dataset zip file) into the Files panel on the left sidebar.
5. Click **Runtime** -> **Run all** to run the complete pipeline.

### Local Setup
To run this project locally, ensure you have Python 3.10+ installed.

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/steel-defect-classification.git
   cd steel-defect-classification
   ```

2. Install dependencies:
   ```bash
   pip install torch torchvision optuna matplotlib numpy scikit-learn
   ```

3. Ensure the dataset `archive (4).zip` is located in the root directory.

4. Open VS Code or Jupyter:
   ```bash
   jupyter notebook SmartForge_Defect_Detection.ipynb
   ```

---

## 📈 Summary of Results

- **ReLU Convergence**: ReLU networks outperformed Sigmoid networks in training speed, reaching stable loss profiles in under 10 epochs.
- **Hardening Gains**: Adding **Data Augmentation + BatchNorm + Dropout** reduced the generalization gap by over 12%, bringing validation accuracy to a stable $\approx 85-89\%$.
- **Class Confusions**: F1-scores revealed that Crazing and Patches are the most common confused classes due to texture similarities under varying lighting angles.
- **Optuna Tuning**: Bayesian search found that an optimal learning rate of $\approx 0.0008$ and a batch size of $32$ yielded the highest validation stability.
