# Use a lightweight Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ETL scripts into container
COPY . .

# Run: wait for both DBs, then load CSVs, then perform ETL
CMD python wait_for_dbs.py && python load_source.py && python etl.py