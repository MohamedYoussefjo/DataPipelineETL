from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from pyspark.sql.functions import col, to_timestamp, when
import os
import shutil
from pyspark.sql import DataFrame
from typing import List

# Directory configuration
INPUT_DIR = "/app/inputcsv"
PROCESSED_DIR = "/app/jobdone"
CHECKPOINT_DIR = "/app/check50"

def move_processed_file(file_path: str) -> None:
    """Déplace un fichier traité vers le répertoire jobdone"""
    try:
        # Nettoyage du chemin (enlève 'file:' si présent)
        clean_path = file_path.replace('file:', '')
        
        # Vérification que le fichier existe
        if not os.path.exists(clean_path):
            print(f"Fichier {clean_path} non trouvé - peut-être déjà déplacé?")
            return

        filename = os.path.basename(clean_path)
        dest_path = os.path.join(PROCESSED_DIR, filename)
        
        # Création du répertoire de destination si inexistant
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        
        # Déplacement du fichier
        shutil.move(clean_path, dest_path)
        print(f"Fichier {filename} déplacé vers {PROCESSED_DIR}")
        
    except Exception as e:
        print(f"Erreur lors du déplacement de {file_path}: {str(e)}")

def process_batch(df: DataFrame, batch_id: int) -> None:
    """Process each micro-batch and move files"""
    if df.rdd.isEmpty():
        return
    
    # Get list of input files processed in this batch
    input_files = df.inputFiles()
    print(f"Processing batch {batch_id} with files: {input_files}")
    
    # Processing logic
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
    
    # Move processed files one by one
    for file_path in input_files:
        move_processed_files(file_path)

if __name__ == "__main__":
    # Initialize Spark session
    spark = SparkSession.builder \
        .appName("Real-Time CSV Processing to Kafka with File Movement") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5") \
        .getOrCreate()

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

    # Read streaming data from INPUT_DIR
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
