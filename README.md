# Predicting Time to Solve Tasks (TtST) in GitHub Issues

## Description
This project explores innovative methods for predicting Time to Solve Tasks (TtST) in managing open issues on platforms like GitHub. It uses machine learning techniques, including a Random Forest classifier and a Large Language Model (LLM), to predict issue resolution times based on various features extracted from GitHub issues and pull requests.

## Project Structure
- `text_data.ipynb`: Jupyter notebook for processing text data and implementing the Large Language Model (LLM).
- `non_text_data.ipynb`: Jupyter notebook for processing non-text data and implementing the Random Forest classifier.
- `requirements.txt`: List of required Python packages.

## Installation
1. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

### Processing Text Data
1. Open the `text_data.ipynb` notebook using Jupyter:
   ```sh
   jupyter notebook text_data.ipynb
   ```

2. Follow the steps in the notebook to process the text data and train the Large Language Model (LLM). This includes:
   - Loading and preprocessing the text data.
   - Fine-tuning the LLM.
   - Evaluating the model on test data.

### Processing Non-Text Data
1. Open the `non_text_data.ipynb` notebook using Jupyter:
   ```sh
   jupyter notebook non_text_data.ipynb
   ```

2. Follow the steps in the notebook to process the non-text data and train the Random Forest classifier. This includes:
   - Loading and preprocessing the non-text data.
   - Feature selection and engineering.
   - Training the Random Forest classifier.
   - Evaluating the model on test data.

## Citation
If you use this code, please cite the Zenodo record:
[![DOI](https://zenodo.org/badge/804013389.svg)](https://zenodo.org/doi/10.5281/zenodo.12661714)


## Acknowledgments
Special thanks to the contributors of the freeCodeCamp repository and the open-source community.
```

