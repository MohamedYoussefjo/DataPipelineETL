from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
from pyspark.sql.functions import col, to_timestamp, when, lit, struct, to_json
import os
import shutil
import hashlib
from datetime import datetime
from glob import glob
import atexit
import socket 



s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ip=s.getsockname()[0]
s.close()

# ===== Configuration =====
INPUT_DIR = "/app/csv/inputcsv"
PROCESSED_DIR = "/app/csv/jobdone"
BACKUP_DIR = "/app/csv/backups"
CHECKPOINT_DIR = "/app/csv/check50"
KAFKA_BROKER = f"{ip}:9092"
KAFKA_TOPIC = "csv"

# Ensure directories exist
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# ===== Helper Functions =====
def backup_file(src_path: str) -> bool:
    """Create a backup with MD5 hash deduplication."""
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
        for backup in glob(os.path.join(BACKUP_DIR, f"backup_*_{filename}")):
            with open(backup, 'rb') as f:
                if hashlib.md5(f.read()).hexdigest() == file_hash:
                    print(f"Skipping duplicate: {filename}")
                    return True

        # Create new backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}_{filename}")
        shutil.copy2(clean_path, backup_path)
        print(f"Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"Backup failed for {src_path}: {str(e)}")
        return False

def move_processed_file(file_path: str) -> bool:
    """Move processed file to the archive directory."""
    try:
        clean_path = file_path.replace('file:', '')
        if not os.path.exists(clean_path):
            print(f"File not found: {clean_path}")
            return False

        filename = os.path.basename(clean_path)
        dest_path = os.path.join(PROCESSED_DIR, filename)
        
        # Atomic move (works within same filesystem)
        shutil.move(clean_path, dest_path)
        print(f"Moved to processed: {dest_path}")
        return True
    except Exception as e:
        print(f"Failed to move {file_path}: {str(e)}")
        return False

# ===== Spark Streaming Logic =====
def process_batch(df: DataFrame, batch_id: int) -> None:
    """Process each micro-batch with backup and Kafka write."""
    if df.isEmpty():
        print(f"Batch {batch_id} was empty. Skipping.")
        return

    input_files = df.inputFiles()
    print(f"Processing batch {batch_id} | Files: {input_files}")

    # Step 1: Backup all files first
    backup_results = [backup_file(f) for f in input_files]
    if not all(backup_results):
        failed_files = [f for f, success in zip(input_files, backup_results) if not success]
        print(f"Aborting batch due to backup failures: {failed_files}")
        return

    # Step 2: Process data
    cleaned_df = (
        df
        .withColumn("Time", to_timestamp(col("Time"), "MM-dd-yyyy HH:mm"))
        .na.fill(0, subset=["Downlink EARFCN", "LocalCell Id"])
        .na.fill("N/A", subset=["eNodeB Name", "Cell Name"])
        .filter(col("Latitude").isNotNull() & col("Longitude").isNotNull())
        .withColumn("Downlink bandwidth", 
                   when(col("Downlink bandwidth") == "NULL", "0")
                   .otherwise(col("Downlink bandwidth")))
        .drop("Integrity")
    )

    # Step 3: Write to Kafka
    try:
        (
            cleaned_df
            .select(
                lit(batch_id).alias("key"),
                to_json(struct(*cleaned_df.columns)).alias("value")
            )
            .write
            .format("kafka")
            .option("kafka.bootstrap.servers", KAFKA_BROKER)
            .option("topic", KAFKA_TOPIC)
            .mode("append")
            .save()
        )
        print(f"Successfully wrote batch {batch_id} to Kafka")
    except Exception as e:
        print(f"Kafka write failed for batch {batch_id}: {str(e)}")
        return  # Skip file movement if Kafka fails

    # Step 4: Move processed files
    move_results = [move_processed_file(f) for f in input_files]
    if not all(move_results):
        failed_moves = [f for f, success in zip(input_files, move_results) if not success]
        print(f"Failed to move files: {failed_moves}")

# ===== Main Execution =====
if __name__ == "__main__":
    # Initialize Spark with Kafka support
    spark = (
        SparkSession.builder
        .appName("Real-Time CSV-to-Kafka Processor")
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5")
        .config("spark.sql.streaming.schemaInference", "true") 
        .config("spark.sql.files.maxPartitionBytes", "128MB")  # Default 128MB is too small
        .config("spark.sql.shuffle.partitions", "4")  # Adjust based on cores (e.g., num_executors * cores_per_executor * 2)
        .config("spark.executor.instances", "1")  # Increase for 5GB+ files
        .config("spark.executor.memory", "2g")  # Increase for 5GB+ files
        .config("spark.driver.memory", "2g")
        .config("spark.executor.cores", "2")  # Parallelism within executors
        .config("spark.task.maxFailures", "4")  # Retry failed tasks
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # Define schema (adjust fields as needed)
    schema = StructType([
    StructField("Time", StringType(), True),
    StructField("eNodeB Name", StringType(), True),
    StructField("Frequency band", StringType(), True),
    StructField("Cell FDD TDD Indication", StringType(), True),
    StructField("Cell Name", StringType(), True),
    StructField("Downlink EARFCN", IntegerType(), True),
    StructField("Downlink bandwidth", IntegerType(), True),
    StructField("LTECell Tx and Rx Mode", StringType(), True),
    StructField("LocalCell Id", IntegerType(), True),
    StructField("eNodeB Function Name", StringType(), True),
    StructField("Latitude", DoubleType(), True),
    StructField("Longitude", DoubleType(), True),
    StructField("Integrity", StringType(), True),
    StructField("FT_AVE 4G/LTE DL USER THRPUT without Last TTI(ALL) (KBPS)(kbit/s)", DoubleType(), True),
    StructField("FT_AVERAGE NB OF USERS (UEs RRC CONNECTED)", IntegerType(), True),
    StructField("FT_PHYSICAL RESOURCE BLOCKS LOAD DL(%)", DoubleType(), True),
    StructField("FT_PHYSICAL RESOURCE BLOCKS LOAD UL", DoubleType(), True),
    StructField("FT_4G/LTE DL TRAFFIC VOLUME (GBYTES)", DoubleType(), True),
    StructField("FT_4G/LTE DL&UL TRAFFIC VOLUME (GBYTES)", DoubleType(), True),
    StructField("FT_4G/LTE UL TRAFFIC VOLUME (GBYTES)", DoubleType(), True),
    StructField("FT_4G/LTE CONGESTED CELLS RATE", DoubleType(), True),
    StructField("FT_4G/LTE CALL SETUP SUCCESS RATE", DoubleType(), True),
    StructField("FT_4G/LTE AVERAGE REPORTED CQI", DoubleType(), True),
    StructField("FT_4G/LTE PAGING DISCARD RATE", DoubleType(), True),
    StructField("FT_4G/LTE RADIO DOWNLINK DELAY(ms)", DoubleType(), True),
    StructField("FT_4G/LTE VOLTE TRAFFIC VOLUME (GBYTES)", DoubleType(), True),
    StructField("FT_AVE 4G/LTE DL USER THRPUT (ALL) (KBPS)(kB/s)", DoubleType(), True),
    StructField("FT_AVE 4G/LTE DL THRPUT (ALL) (KBITS/SEC)", DoubleType(), True),
    StructField("FT_AVERAGE NB OF CA UEs RRC CONNECTED(number)", IntegerType(), True),
    StructField("FT_AVERAGE NUMBER OF UE QUEUED DL", IntegerType(), True),
    StructField("FT_AVERAGE NUMBER OF UE QUEUED UL", IntegerType(), True),
    StructField("FT_S1 SUCCESS RATE", DoubleType(), True),
    StructField("FT_UL.Interference", DoubleType(), True),
    StructField("Average Nb of e-RAB per UE", DoubleType(), True),
    StructField("Average Nb of PRB used per Ue", DoubleType(), True),
    StructField("Average Nb of Used PRB for SRB", DoubleType(), True),
    StructField("FT_AVERAGE NUMBER OF UE SCHEDULED PER ACTIVE TTI DL (FDD)(number)", IntegerType(), True),
    StructField("FT_AVERAGE NUMBER OF UE SCHEDULED PER ACTIVE TTI UL (TDD)", IntegerType(), True),
    StructField("FT_CS FALLBACK SUCCESS RATE (4G SIDE ONLY)", DoubleType(), True),
    StructField("FT_CS FALLBACK TO WCDMA RATIO", DoubleType(), True),
    StructField("FT_ERAB SETUP SUCCESS RATE", DoubleType(), True),
    StructField("FT_ERAB SETUP SUCCESS RATE (ALL)(%)", DoubleType(), True),
    StructField("FT_ERAB SETUP SUCCESS RATE (init)", DoubleType(), True),
    StructField("FT_RRC SUCCESS RATE", DoubleType(), True),
    StructField("Nb e-RAB Setup Fail", IntegerType(), True),
    StructField("Nb HO fail to GERAN", IntegerType(), True),
    StructField("Nb HO fail to UTRA FDD", IntegerType(), True),
    StructField("Nb initial e-RAB Setup Fail", IntegerType(), True),
    StructField("Nb initial e-RAB Setup Succ", IntegerType(), True),
    StructField("Nb initial e-RAB Sucess rate(%)", DoubleType(), True),
    StructField("Nb of HO over S1 for e-RAB Fail", IntegerType(), True),
    StructField("Nb of HO over S1 for e-RAB Req", IntegerType(), True),
    StructField("Nb of HO over S1 for e-RAB Succ", IntegerType(), True),
    StructField("Nb of HO over X2 for e-RAB Fail", IntegerType(), True),
    StructField("Nb of HO over X2 for e-RAB Succ", IntegerType(), True),
    StructField("Nb of RRC connection release", IntegerType(), True),
    StructField("Nb S1 Add e-RAB Setup fail", IntegerType(), True),
    StructField("RRC Emergency SR", DoubleType(), True),
    StructField("RRC High Priority SR(%)", DoubleType(), True),
    StructField("RRC MOC SR(%)", DoubleType(), True),
    StructField("RRC MTC SR(%)", DoubleType(), True),
    StructField("RRC Succ rate(%)", DoubleType(), True),
    StructField("CSFB failure rate(%)", DoubleType(), True),
    StructField("E-RAB Resource Congestion Rate(%)", DoubleType(), True),
    StructField("RRC Resource Congestion Rate(%)", DoubleType(), True),
    StructField("Average TA", DoubleType(), True),
    StructField("AVE 4G/LTE UL USER THRPUT without Last TTI (Kbps)", DoubleType(), True)
])

    # Start streaming query
    streaming_df = (
        spark.readStream
        .schema(schema)
        .option("header", "true")
        .option("maxFilesPerTrigger", 1)  # Process files one-by-one
        .option("cleanSource", "delete")  # Auto-delete files after processing
        .csv(INPUT_DIR)
    )

    # Graceful shutdown handler
    atexit.register(lambda: spark.stop())

    # Start the stream
    query = (
        streaming_df
        .writeStream
        .foreachBatch(process_batch)
        .option("checkpointLocation", CHECKPOINT_DIR)
        .outputMode("append")
        .start()
    )

    print("Streaming started. Waiting for new files...")
    query.awaitTermination()