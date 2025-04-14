from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_json, struct, when, input_file_name
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
import os
import shutil
from datetime import datetime
from glob import glob

def get_config_value(spark, key):
    return spark.sparkContext.getConf().get("spark.driver.extraJavaOptions", "").split(f"-D{key}=")[-1].split(" ")[0]

def ensure_dirs(*dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def backup_file(src_path, backup_dir):
    """Create timestamped backup copy"""
    if not os.path.exists(src_path):
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(src_path)
    backup_path = os.path.join(backup_dir, f"backup_{timestamp}_{filename}")
    
    shutil.copy2(src_path, backup_path)
    print(f"Created backup: {backup_path}")
    return True

def move_to_processed(src_path, processed_dir):
    """Move file to processed with timestamp"""
    if not os.path.exists(src_path):
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(src_path)
    processed_path = os.path.join(processed_dir, f"processed_{timestamp}_{filename}")
    
    shutil.move(src_path, processed_path)
    print(f"Moved to processed: {processed_path}")
    return True

def main():
    spark = SparkSession.builder \
        .appName("JSON-to-Kafka-Stream") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5") \
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
        .getOrCreate()

    # Get config values
    json_input_dir = get_config_value(spark, "json.input.dir")
    json_processed_dir = get_config_value(spark, "json.processed.dir")
    json_backup_dir = get_config_value(spark, "json.backup.dir")
    checkpoint_dir = "/app/checkpointxmlonly"
    
    ensure_dirs(json_processed_dir, json_backup_dir, checkpoint_dir)

    # Schema definition
    schema = StructType([
        StructField("measInfoId", StringType(), nullable=False),
        StructField("jobId", StringType(), nullable=False),
        StructField("granPeriod", StringType(), nullable=False),
        StructField("beginTime", StringType(), nullable=False),
        StructField("endTime", StringType(), nullable=False),
        StructField("measObjLdn", StringType(), nullable=False),
        StructField("kpiId", StringType(), nullable=False),
        StructField("kpiName", StringType(), nullable=False),
        StructField("kpiValue", StringType(), nullable=False)
    ])

    # Track processed files
    processed_files = set()

    # Process each batch
    def process_batch(df, batch_id):
        nonlocal processed_files
        if df.isEmpty():
            print("No data in batch")
            return
        
        # Get unique source files in this batch
        input_files = [row['input_file'] for row in df.select("input_file").distinct().collect()]
        clean_files = []
        
        for file_path in input_files:
            # Remove Spark file:// prefix if present
            clean_path = file_path[5:] if "file:" in file_path else file_path
            clean_files.append(clean_path)
            
            # Backup first
            backup_file(clean_path, json_backup_dir)
        
        # Transform and write to Kafka
        (df.withColumn("kpiValue", when(col("kpiValue") == "NIL", 0).otherwise(col("kpiValue").cast("integer")))
          .select(to_json(struct([col(c) for c in df.columns if c != "input_file"])).alias("value"))
          .write
          .format("kafka")
          .option("kafka.bootstrap.servers", "192.168.253.129:9092")
          .option("topic", "xmlt_fast")
          .save()
        )
        
        # Move to processed immediately
        for clean_path in clean_files:
            if move_to_processed(clean_path, json_processed_dir):
                processed_files.add(clean_path)
        
        print(f"Processed batch {batch_id} from files: {clean_files}")

    # Create streaming DataFrame with file path tracking
    streaming_df = spark.readStream \
        .schema(schema) \
        .option("multiline", "true") \
        .option("maxFilesPerTrigger", 1) \
        .json(json_input_dir) \
        .withColumn("input_file", input_file_name())

    # Start streaming query
    query = streaming_df.writeStream.foreachBatch(process_batch).option("checkpointLocation", checkpoint_dir).trigger(once=True).start()

    # Wait for completion
    query.awaitTermination()
    
    # Verify all expected files were processed
    input_files = set(glob(os.path.join(json_input_dir, "*.json")))
    if input_files - processed_files:
        print(f"Warning: Some files weren't processed: {input_files - processed_files}")
    
    spark.stop()
    print(f"Stream processing completed. Processed {len(processed_files)} files.")

if __name__ == "__main__":
    main()
