from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from pyspark.sql.functions import col, to_timestamp, when
import os
import shutil
import hashlib
from pyspark.sql import DataFrame
from typing import List
from glob import glob
from datetime import datetime

# Directory configuration
INPUT_DIR = "/app/inputcsv"
PROCESSED_DIR = "/app/jobdone"
BACKUP_DIR = "/app/backups"  # New backup directory
CHECKPOINT_DIR = "/app/check50"

def ensure_dirs(*dirs):
    """Ensure directories exist"""
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def backup_file(src_path: str) -> bool:
    """Create backup with duplicate prevention"""
    try:
        clean_path = src_path.replace('file:', '')
        if not os.path.exists(clean_path):
            print(f"File not found: {clean_path}")
            return False

        # Calculate file hash
        with open(clean_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()

        filename = os.path.basename(clean_path)
        
        # Check for existing backups with same content
        existing_backups = glob(os.path.join(BACKUP_DIR, f"backup_*_{filename}"))
        for backup in existing_backups:
            try:
                with open(backup, 'rb') as f:
                    if hashlib.md5(f.read()).hexdigest() == file_hash:
                        print(f"Duplicate found - skipping backup for {filename}")
                        return True  # Considered success but no new backup
            except Exception as e:
                print(f"Error checking backup {backup}: {str(e)}")
                continue

        # Create new backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}_{filename}")
        shutil.copy2(clean_path, backup_path)
        print(f"Created backup: {backup_path}")
        return True

    except Exception as e:
        print(f"Error creating backup: {str(e)}")
        return False

def move_processed_file(file_path: str) -> bool:
    """Move processed file to destination directory"""
    try:
        clean_path = file_path.replace('file:', '')
        if not os.path.exists(clean_path):
            print(f"File not found: {clean_path}")
            return False

        filename = os.path.basename(clean_path)
        dest_path = os.path.join(PROCESSED_DIR, filename)
        
        shutil.move(clean_path, dest_path)
        print(f"Moved to processed: {dest_path}")
        return True
        
    except Exception as e:
        print(f"Error moving file: {str(e)}")
        return False

def process_batch(df: DataFrame, batch_id: int) -> None:
    """Process each micro-batch with backup and file movement"""
    if df.rdd.isEmpty():
        return
    
    input_files = df.inputFiles()
    print(f"Processing batch {batch_id} with files: {input_files}")
    
    # Create backups first
    backup_failures = []
    for file_path in input_files:
        if not backup_file(file_path):
            backup_failures.append(file_path)
    
    if backup_failures:
        print(f"Skipping processing due to backup failures for: {backup_failures}")
        return
    
    # Data processing
    cleaned_df = df.withColumn("Time", to_timestamp(col("Time"), "MM-dd-yyyy HH:mm")) \
        .na.fill(0, subset=["Downlink EARFCN", "LocalCell Id"]) \
        .na.fill("N/A", subset=["eNodeB Name", "Cell Name"]) \
        .filter(col("Latitude").isNotNull() & col("Longitude").isNotNull()) \
        .withColumn("Downlink bandwidth", 
                   when(col("Downlink bandwidth") == "NULL", "0")
                   .otherwise(col("Downlink bandwidth"))) \
        .drop("Integrity")
    
    # Write to Kafka
    cleaned_df.selectExpr("CAST(Time AS STRING) AS key", "to_json(struct(*)) AS value") \
        .write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "192.168.253.129:9092") \
        .option("topic", "csv") \
        .save()
    
    # Move processed files
    for file_path in input_files:
        if not move_processed_file(file_path):
            print(f"Failed to move file: {file_path}")

if __name__ == "__main__":
    # Initialize directories
    ensure_dirs(INPUT_DIR, PROCESSED_DIR, BACKUP_DIR, CHECKPOINT_DIR)

    # Initialize Spark session
    spark = SparkSession.builder \
        .appName("Real-Time CSV Processing to Kafka with Backup") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5") \
        .getOrCreate()

    # Schema definition (unchanged from your original)
    schema = StructType([
        StructField("Time", StringType(), True),
        StructField("eNodeB Name", StringType(), True),
        # ... (rest of your schema fields remain exactly the same)
        StructField("AVE 4G/LTE UL USER THRPUT without Last TTI (Kbps)", DoubleType(), True)
    ])

    # Read streaming data
    streaming_df = spark.readStream \
        .schema(schema) \
        .option("header", True) \
        .option("sep", ",") \
        .option("ignoreLeadingWhiteSpace", "true") \
        .option("cleanSource", "off") \
        .csv(INPUT_DIR)

    # Start streaming query
    query = streaming_df \
        .writeStream \
        .foreachBatch(process_batch) \
        .option("checkpointLocation", CHECKPOINT_DIR) \
        .trigger(once=True) \
        .start()

    query.awaitTermination()
