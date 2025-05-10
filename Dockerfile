FROM apache/airflow:2.7.3-python3.11

# System configuration
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        procps \
        openjdk-11-jdk \
        ca-certificates \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set Java environment
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Switch to airflow user for Python packages
USER airflow
WORKDIR /home/airflow

# Install all Python packages directly in Dockerfile
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
        pyspark==3.5.0 \
        requests \
        apache-airflow-providers-apache-spark \
        lxml \
        python-decouple \
        pandas \
        apache-airflow-providers-http \
        "apache-airflow-providers-openlineage>=1.8.0"

# Final configuration
USER airflow
ENV PYTHONPATH="${PYTHONPATH}:/home/airflow/.local/lib/python3.11/site-packages"
