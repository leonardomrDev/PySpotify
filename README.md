# PySpotify Data Engineering Project

This project is the documentation and the results of months of Data Engineering, Data Analysis and AWS Cloud Architecture. The goal is to develop an entire aws cloud-based ETL (Extract, Transform and Load) pipeline, for now, only the first part of the pipeline has been created, the script. However, the cloud infrastructure that is planned to be soon implemented is the following:

## The AWS Cloud Architecture Solution

Work in progress...

![image](https://github.com/leonardomrDev/PySpotify/assets/77642648/20f5fe31-d597-4274-a55e-eaf5f6afe950)

<h1 align="center">
PySpotify Data Engineering Project
</h1>


<h4 align="center"> 
:construction: DOCUMENTAÇÃO EM CONSTRUÇÃO :construction:
</h4>


## Summary

- Description and Objective

- Technologies

- Cloud Infrastructure

- Instructions for Execution

- Project Planning and Authorship


## Description and Objective

The main idea behind this project is to work with and integrate various AWS services that I didn't have experience with, as well as to enhance my skills and knowledge in developing and maintaining ETL pipelines in the cloud.

However, that's not the sole objective. I aim to have the complete process, from designing the infrastructure architecture, its development, data extraction, processing, transformation, loading, and, most importantly for the project's success, the automation/scheduling of the previous processes.

### What's the reason for choosing to use the Spotify API?

This project was extremely important to motivate my studies and establish a disciplined routine of studying every day. I identified that what was lacking for this motivation was precisely a project where the end product would be interesting to me. So, having this view of the most played songs on Spotify, with weekly updates, is what brings that extra enthusiasm to study.

## Technologies

### Technologies utilized for the local development:

- Python 3.11
- VSCode
- Spotipy
- Pandas
- numpy
- boto3

### Technologies utilized for the cloud development:

- Python 3.7
- Spotipy
- numpy
- Pandas
- boto3
- Amazon Web Services (AWS)
- IAM
- S3
- SecretsManager
- Lambda
- EventBridge
- Glue
- Athena
- QuickSight (Em desenvolvimento) (To-Do)

It's important to emphasize, before presenting the architectural decisions, that it wasn't part of my goal to develop an "optimized" infrastructure. As mentioned earlier, the project was intended to learn about other tools/services that are widely used in data-driven cloud infrastructures.

## Cloud Infrastructure:

### AWS Simple Storage Service (S3)

One of the most widely used AWS services, and because it's more than just storage, it's also used as a bridge between services, and that's exactly how I use it here. In addition to storing the Python packages that the Lambda spotipy layer uses, the final result of the lambda script execution is to send the generated .csv to S3 (spotify-dataops-raw), such result also occurs with the Glue ETL Job, the .parquet files the process creates are sent to an s3 bucket (spotify-dataops-refined), so that a catalog and tables may be created.

### AWS IAM

Without a doubt, a crucial service, not only in terms of data protection by limiting access but also crucial for integrating services. We can assign roles or permissions to various AWS services to enable them to interact with each other. An example of this interaction is the spotify_secrets_manager permission role, which allows the lambda to utilize the client_id and client_secret variables spotipy lib requires to establish a successful connection with the spotify api.

### AWS Lambda

For lightweight and quick scripts, Lambda is a much better choice than EC2. It's the perfect choice for a quick web scraping or a modest data collection. In the project's case, the execution time is around 8 minutes, well below the 15-minute limit. However, the problem was dealing with the script's size, which, due to the various libraries used, was 297MB (Remember that Lambda has a 250MB limit). Initially, I tried to use Pandas in a layer, but the layer's limit made this impossible. After some research, I found a permanent solution, which was to abandon the Lambda with Python 3.11 and use version 3.7 in the Lambda, which has an AWS layer with Pandas and Numpy included. With this change, I was able to add pyspotify in a second layer and only the Python script and a .cache file from spotipy in the root of the Lambda.

### AWS Secrets Manager

When it comes to interacting with APIs, it is of paramount importance to keep access tokens and secrets secure. To achieve this, I decided to implement the use of this service in my extraction code:

```python
# Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import boto3
from botocore.exceptions import ClientError

def get_secret():

    secret_name = "PySpotify"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']

    # Your code goes here.
```

It was extremely straightforward to implement it in my code; having the provided code significantly expedited and simplified the implementation, ending up being even simpler than implementing the token and secret as environment variables.

### AWS Eventbridge/AWS Events

A critical service for automating/scheduling the Lambda's initialization and the execution of the data extraction script.

### AWS Glue

I use Glue primarily to create a data catalog with two tables for the raw files (csv). These two tables are created using a scheduled crawler that runs every noon; this crawler collects the data available in the S3 bucket (spotify-dataops-raw). Afterward, I use Glue to execute a Python script with an ETL Job, the purpose of which is to transform the raw files (csv) into refined ones (parquet) and deposit them into the S3 bucket (spotify-dataops-refined). Even though it may not be necessary due to the data volume not being substantial, the goal is to test and comprehend how this process functions. This ETL also has a schedule; it runs a few minutes after the crawler that creates the raw data catalog. To complete this parquet transformation process, there's a crawler that gathers refined data from S3 and creates a new data catalog containing the tables in parquet format.

For this parquet transformation process, we employ the following code in the ETL Job:

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

# Init GlueContext
args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Função que irá transformar um .csv para .parquet
def transform_csv_to_parquet(database, table_name):
    # Leitura dos dados do Glue DataCatalog
    data_frame = glueContext.create_dynamic_frame.from_catalog(
        database=database,
        table_name=table_name,
    )
    
    # Mapeamento dos dados
    transformed_data_frame = ApplyMapping.apply(
        frame=data_frame,
        mappings=[
            ("artist", "string", "artist", "string"),
            ("track", "string", "track", "string"),
            ("track_pop", "bigint", "track_pop", "bigint"),
            ("duration_ms", "bigint", "duration_ms", "bigint"),
            ("album_nm", "string", "album_nm", "string"),
            ("album_dt", "string", "album_dt", "string")
        ],
    )
    
    # Converte de DynamicFrame para DataFrame
    data_frame_df = transformed_data_frame.toDF()
    
    # Envio do DataFrame em parquet ao S3
    parquet_file_name = table_name + "_refined"
    data_frame_df.write.parquet("s3://spotify-dataops-refined/" + parquet_file_name, mode="overwrite")

# Chama a função de transformação das tabelas
transform_csv_to_parquet("spotify_data", "spotifypopularsongs")
transform_csv_to_parquet("spotify_data", "spotifytopplayed")

# Commit do ETL Job
job.commit()
```

### AWS Athena

With the creation of the DataCatalogs, I was able to integrate Athena into the infrastructure, enabling the writing of SQL queries.

## Execution Instructions

To run this code locally, it's quite simple. First, you need to create a Python virtual environment. There are several ways to do this, but I would say the best way is to use Poetry.

The following tutorial will be for running the extraction code in the classic venv.

The first step is to install Python. I used version 3.11 because the latest version at the time didn't have all the necessary dependencies for the project.

Next, we'll create our virtual environment (Virtual Environment). We can do this with the following command:

python -m venv <nome-do-ambiente>

This command will create our environment using the most recent version of Python installed on the local machine.

With the environment created, you should have the following directory structure:

```
> /[pasta-projeto]/
	> main.py (os outros .py são dedicados para utilização na AWS)
	> requirements.txt
	> <nome-da-venv>
	> <csvs-gerados>
```

Having this, or something similar, you still need the libraries. To simplify their installation, I created a .txt file using pip freeze containing all the libraries from my virtual environment.

To install them, you need to be in the project directory, open the cmd, and activate the virtual environment as follows:

<venv>/Scripts/Activate.bat

Then, run the following command in your terminal/cmd:

pip install -r requirements.txt

After installing all the dependencies/requirements, you'll need your Spotify API Client ID and Secret, which you should replace where indicated in the extraction script <main.py>.

## Project Planning and Authorship

Leonardo Martins - Data Analyst (Seeking experience in data architecture and engineering)
