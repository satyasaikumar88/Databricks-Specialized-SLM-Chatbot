from __future__ import annotations

import json
from pathlib import Path


DATASET = [
    {
        "question": "What is Delta Lake?",
        "answer": "Delta Lake is an open storage layer that adds ACID transactions, schema enforcement, and time travel to data lakes. It is the foundation of the Databricks lakehouse architecture and is used to build reliable Bronze, Silver, and Gold data pipelines.",
        "category": "core",
        "source": "https://docs.databricks.com/en/delta/index.html",
    },
    {
        "question": "Explain Bronze, Silver and Gold architecture.",
        "answer": "The medallion architecture is a layered approach to data processing. Bronze stores raw ingested data; Silver stores validated and cleaned data with business rules applied; Gold stores curated and analytics-ready data used by dashboards, BI, and ML. This architecture keeps raw data intact while providing trusted downstream datasets.",
        "category": "lakehouse",
        "source": "https://docs.databricks.com/en/lakehouse/architecture.html",
    },
    {
        "question": "What is Unity Catalog?",
        "answer": "Unity Catalog is Databricks' unified governance solution for data, AI, and analytics assets. It centralizes permissions, lineage, and discovery, and organizes data assets into catalogs, schemas, and tables with fine-grained access controls.",
        "category": "governance",
        "source": "https://docs.databricks.com/en/data-governance/unity-catalog/index.html",
    },
    {
        "question": "Why is my Spark job slow?",
        "answer": "Common causes of slow Spark jobs include data skew, too many small files, expensive shuffles, poor partitioning, and under-sized clusters. In Databricks, review the Spark UI for stage duration, shuffle read/write, spilled data, and input file counts, then optimize partitioning, joins, and file sizes.",
        "category": "performance",
        "source": "https://docs.databricks.com/en/optimizations/index.html",
    },
    {
        "question": "Write PySpark code to create a Delta table.",
        "answer": "from pyspark.sql import SparkSession\n\nspark = SparkSession.builder.appName(\"delta-demo\").getOrCreate()\n\ndata = [(1, \"Alice\", 1000), (2, \"Bob\", 950)]\ncolumns = [\"id\", \"name\", \"salary\"]\ndf = spark.createDataFrame(data, columns)\ndf.write.format(\"delta\").mode(\"overwrite\").save(\"/tmp/delta_demo\")\nprint(\"Delta table created at /tmp/delta_demo\")\n",
        "category": "pyspark",
        "source": "https://docs.databricks.com/en/delta/quickstart.html",
    },
    {
        "question": "What is Auto Loader?",
        "answer": "Auto Loader is Databricks' incremental ingestion capability for cloud storage. It can detect new files and load them into Delta tables without reprocessing historical data, making it well-suited for near-real-time ingestion from S3, ADLS, or GCS.",
        "category": "ingestion",
        "source": "https://docs.databricks.com/en/ingestion/auto-loader/index.html",
    },
    {
        "question": "What is MLflow?",
        "answer": "MLflow is an open-source platform for tracking experiments, packaging ML code, and managing model lifecycle tasks. On Databricks, MLflow integrates with notebooks, jobs, and the model registry to support reproducible ML workflows.",
        "category": "mlops",
        "source": "https://mlflow.org/docs/latest/index.html",
    },
    {
        "question": "What is Databricks SQL?",
        "answer": "Databricks SQL is a serverless SQL experience for querying data in the lakehouse using familiar SQL tools and dashboards. It provides governed access to curated and semantic layers without requiring custom Spark jobs for each ad hoc query.",
        "category": "sql",
        "source": "https://docs.databricks.com/en/sql/index.html",
    },
    {
        "question": "What is a lakehouse?",
        "answer": "A lakehouse combines the scalability and low cost of a data lake with the reliability and performance of a warehouse. Databricks implements this by pairing Delta Lake, Spark, and Unity Catalog with governance and analytics capabilities.",
        "category": "lakehouse",
        "source": "https://docs.databricks.com/en/lakehouse/index.html",
    },
    {
        "question": "What is schema enforcement in Delta Lake?",
        "answer": "Schema enforcement ensures that a Delta table rejects incompatible writes that do not match the table's expected schema. This helps maintain data quality and prevents silent corruption from invalid record shapes.",
        "category": "delta",
        "source": "https://docs.databricks.com/en/delta/index.html",
    },
    {
        "question": "What is a broadcast join in Spark?",
        "answer": "A broadcast join sends the smaller side of a join to each worker node so the join can happen locally, avoiding a large shuffle. It is effective when one dataset is much smaller than the other and can dramatically reduce join cost.",
        "category": "spark",
        "source": "https://docs.databricks.com/en/optimizations/joins.html",
    },
    {
        "question": "Explain the medallion architecture.",
        "answer": "The medallion architecture is a progression of data refinement: Bronze keeps raw ingested data, Silver improves quality and validation, and Gold provides curated business-ready datasets. This gives teams a clean approach to data quality and analytics lineage.",
        "category": "lakehouse",
        "source": "https://docs.databricks.com/en/lakehouse/architecture.html",
    },
    {
        "question": "How do I read a Delta table in PySpark?",
        "answer": "Use the Delta format when reading: df = spark.read.format(\"delta\").load(\"/tmp/delta_demo\")\nYou can also register the table in the catalog and query it with SQL.",
        "category": "pyspark",
        "source": "https://docs.databricks.com/en/delta/quickstart.html",
    },
    {
        "question": "What is the difference between a DataFrame and a Spark SQL table?",
        "answer": "A DataFrame is a distributed collection of structured data with operations exposed via Spark APIs. A Spark SQL table is a cataloged relation you can query using SQL. In Databricks, many DataFrames are built from Delta tables and registered as SQL tables.",
        "category": "spark",
        "source": "https://docs.databricks.com/en/sql/index.html",
    },
    {
        "question": "How can I optimize a Delta table?",
        "answer": "Common optimization techniques include compacting small files with OPTIMIZE, using ZORDER BY on frequently filtered columns, and keeping partitions sized appropriately. These techniques improve query performance and reduce cluster overhead.",
        "category": "delta",
        "source": "https://docs.databricks.com/en/delta/optimizations.html",
    },
]


def build_dataset(output_path: str | Path = 'data/databricks_qa.jsonl') -> Path:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open('w', encoding='utf-8') as f:
        for row in DATASET:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    print(f'Wrote {len(DATASET)} rows to {output_file}')
    return output_file


if __name__ == '__main__':
    build_dataset()
