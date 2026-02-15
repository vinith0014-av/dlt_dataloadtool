# Install dependencies for SQL Server
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    unixodbc \
    unixodbc-dev \
    wget \
    unzip \
    libaio-dev \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft repository with signed key
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18


# Oracle Instant Client
RUN wget https://download.oracle.com/otn_software/linux/instantclient/2112000/instantclient-basiclite-linux.x64-21.12.0.0.0dbru.zip && \
    unzip instantclient-basiclite-linux.x64-21.12.0.0.0dbru.zip -d /opt/oracle && \
    echo "/opt/oracle/instantclient_21_12" > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig

# Environment variables
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_12
ENV PATH=$PATH:/opt/oracle/instantclient_21_12

# Python dependencies
RUN pip install --no-cache-dir \
    dlt \
    pyodbc \
    oracledb \
    psycopg2-binary

WORKDIR /app
COPY . /app

CMD ["python", "run_simple.py"]
