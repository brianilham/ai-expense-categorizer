# AI-Powered Expense Categorizer: End-to-End Data Pipeline & BI Dashboard

## Live Dashboard
> **[View the Live Interactive Dashboard Here](https://datastudio.google.com/s/qnY-dLgdh9s)**

## Business Problem & Impact
Manual expense tracking is time-consuming and prone to human error, especially when dealing with raw, unstructured bank statement descriptions (e.g., "QRIS KOPI HOJA", "TRF BURA BURA"). 

This project solves that by building an automated **End-to-End Data Pipeline** that leverages Generative AI to instantly parse, extract, and categorize unstructured transactions. The processed data is then loaded into a cloud database and visualized in a real-time Business Intelligence dashboard, providing immediate insights into financial lifestyle patterns.

## Architecture & Tech Stack
* **Data Ingestion & Wrangling:** Python (`pandas`)
* **AI Classification Engine:** Google Gemini API (`gemini-3.5-flash-lite`) via Prompt Engineering
* **Cloud Data Warehouse:** Supabase (PostgreSQL)
* **Data Visualization & BI:** Google Looker Studio

## Engineering Highlights
* **LLM Batch Processing Optimization:** Redesigned the AI classification architecture from a standard sequential loop (row-by-row execution) to a **JSON-based batch processing model**. 
* **Massive Latency Reduction:** This architectural shift slashed the API processing time from **>5 minutes down to just 30 seconds** for the dataset, eliminating network bottlenecks and significantly optimizing token cost efficiency.
* **Secure Cloud Integration:** Engineered a secure database connection to Supabase using `SQLAlchemy` and `psycopg2`, utilizing `python-dotenv` to isolate and protect database credentials from public exposure.

## How to Run Locally
1. Clone this repository:
   ```bash
   git clone https://github.com/brianilham/ai-expense-categorizer.git

2. Install the required dependencies
   ```bash
   pip install pandas google-generativeai python-dotenv sqlalchemy psycopg2-binary
3. Create a .env file in the root directory and add your API keys and database credentials:
   ```bash
   GEMINI_API_KEY=your_api_key
   user=postgres.[your_project_id]
   password=your_database_password
   host=aws-0-ap-southeast-1.pooler.supabase.com
   port=5432
   dbname=postgres
4. Run the Jupyter Notebook Expense_Categorizer.ipynb to process the raw transaction data and push the AI-categorized results to your Supabase database.
