# Idaho Legislation Analysis

This project scrapes legislative bills from the Idaho Legislature and uses the OpenAI API to detect potential constitutional issues.

---

## Setup

1. **Install [uv](https://docs.astral.sh/uv/getting-started/installation/)** (Python package and project manager).
2. **Sync dependencies** (this also installs the correct Python version automatically):

   ```bash
   uv sync
   ```

---

## Step 1: Scrape Legislative Data

Run the scraper:

```bash
uv run python scrape.py
```

Upon completion, the script will output a string representing the date of the scrape and the directory where the data is stored. This value is referred to as the **`DATARUN`**, and should be exported as an environment variable for use in subsequent steps. For example:

```bash
export DATARUN=04_30_2025
```

---

---

## Step 2: Convert PDFs to HTML

This step converts the downloaded PDF files into HTML while preserving formatting like strikethroughs and underlines, which are essential for interpreting legislative changes. It uses `pdf2docx` for PDF→DOCX conversion and `mammoth` for DOCX→HTML conversion — no external API credentials required.

### Prerequisites

1. Make sure the `DATARUN` environment variable is set:

   ```bash
   export DATARUN=04_30_2025
   ```

### Run the Conversion

Start the conversion process:

```bash
uv run python pdf_to_html.py
```

---

## Step 3: Machine Learning Analysis

After converting PDFs, run the ML analysis to detect constitutional conflicts using OpenAI.

### Prerequisites

1. Ensure `DATARUN` is set:

   ```bash
   export DATARUN=04_30_2025
   ```
2. Set your OpenAI API key (obfuscated):

   ```bash
   export OPENAI_API_KEY="sk-***********************"
   ```

### Run the Analysis

```bash
uv run python ml_analysis.py
```

---

## Step 4: Launch Interactive Dashboard

Finally, start the Streamlit app for visual exploration:

```bash
uv run streamlit run bill_data_explorer.py
```

### See it Live

You can explore the interactive dashboard online here:

[https://danielrmeyer-idaho-legislation-analys-bill-data-explorer-qxzijs.streamlit.app/](https://danielrmeyer-idaho-legislation-analys-bill-data-explorer-qxzijs.streamlit.app/)

---

## Output

All processed data is stored in a subdirectory named after the `DATARUN` value (e.g., `04_30_2025`). This enables archival and comparison of different scrape sessions over time.

---

## Future Goals

* Fine-tune an OpenAI or Mistral model on historical Idaho legislation
* Automatically identify constitutional conflicts in proposed bills
* Provide a searchable legislative history for citizens and advocacy groups

---

## License

This project is open-source. See `LICENSE` for more information.

---

## Contributing

Contributions are welcome! Please open an issue or pull request with ideas or improvements.
