<h1 align="center">
PySpotify Data Engineering Project
</h1>


<h4 align="center"> 
:construction: DOCUMENTAÇÃO EM CONSTRUÇÃO :construction:
</h4>


## Tópicos

- Descrição e Objetivo

- Tecnologias

- Infraestrutura Cloud

- Instruções para Execução

- Planejamento do Projeto e Autoria


## Descrição e Objetivo

A idéia por trás principal desse projeto é; trabalhar com, e realizar a integração de diversos serviços da AWS que eu não possuia experiência, além de aumentar minha experiência e conhecimentos no desenvolvimento e manutenção de pipelines de ETL em cloud.

Mas não é o único objetivo. Quero ter o processo completo, desde a arquitetura da infraestrutura, o desenvolvimento da mesma, a extração de dados, tratamento, transformação, carregamento, automatização/agendamento, e o mais importante para o projeto ser um sucesso; a apresentação dos dados, ou seja, transformar os dados em informação útil com uma visualização utilizando o PowerBI ou o AWS Quicksight.

**Qual o motivo da escolha de utilizar a API do Spotify?**

Esse projeto foi extremamente importante, para ter a motivação para realizar meus estudos e ter, de fato, essa disciplina de todo dia estudar. Identifiquei que o que faltava para essa motivação era justamente um projeto onde o produto resultante fosse interessante para mim. Então ter essa visão das músicas mais tocadas no spotify, com atualização semanal, é o que trás esse ânimo a mais para estudar.

## Tecnologias

### Tecnologias utilizadas para o desenvolvimento local:

- Python 3.11
- VSCode
- Spotipy
- Pandas
- numpy
- boto3

### Tecnologias utilizadas para o desenvolvimento em cloud:

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

É importante ressaltar, antes de apresentar as decisões na arquitetura, que não fazia parte de meu objetivo desenvolver uma infraestrutura "otimizada", como disse anteriormente, o projeto foi para aprender outras ferramentas/serviços que podem e são bastante utilizados em infraestruturas cloud voltada para dados (data driven architecture).

## Infraestrutura Cloud:

### AWS Simple Storage Service (S3)

Um dos serviços mais utilizado da AWS, e por ser mais do que um simples armazenamento, ele também é utilizado como uma ponte entre os serviços, e assim é precisamente como eu o utilizo aqui. Além de armazenar os python packages que o layer spotipy da Lambda utiliza, o resultado final da execução do script lambda é realizar o envio do .csv gerado para o s3 (spotify-dataops-raw) (PAREI AQUI, CONTINUAR DEPOIS)

### AWS IAM

Sem dúvidas o serviço crucial, não apenas no quesito de proteção dos dados ao limitar acessos, mas também ele é crucial para podermos integrar serviços, onde podemos atribuir roles ou permissões para serviços diversos da AWS poderem se utilizar de outros serviços, ou seja, interagirem entre si. Um exemplo dessa interação é a role de permissão spotify-s3, essa role permite os serviços a (CORRIGIR!!!)

### AWS Lambda

Para scripts leves e rápidos, o serviço lambda é uma escolha muito superior ao ec2, é a escolha perfeita para um rápido webscrapping ou uma modesta coleta de dados (não indicado para coletas de bigdata), no caso do projeto, o tempo de execução fica em torno de 8 minutos, bem abaixo do limite de 15 minutos. Porém, o problema foi lidar com o tamanho do script, que por conta das diversas bibliotecas utilizadas ficava em 297MB (Lembrando que a lambda possui um limite de 250MB), primeiramente tentei utilizar o pandas em uma camada, porém, o limite das layers não tornava isso possível, e após um estudo, encontrei a solução permanente, que foi abandonar a lambda com o python 3.11 e utilizar a versão 3.7 na lambda, que possui uma layer aws com o pandas e numpy inclusos. Com essa alteração pude adicionar o pyspotify em uma segunda layer e apenas o script python e um arquivo .cache do spotipy na raiz da lambda.

### AWS Secrets Manager

Quando o assunto é interação com APIs é de suma importância manter em segurança os tokens e secrets de acesso a mesma, e para isso, resolvi implementar em meu código de extração a utilização desse serviço:

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

Foi extremamente simples implementar ele em meu código, o código ser fornecido acaba agilizando e facilitando bastante a implementação, acabou sendo mais simples até do que implementar o token e o secret como variáveis de ambiente.

### AWS Eventbridge/AWS Events

Serviço crucial para realizar a automatização/agendamento da inicialização da lambda e execução do script de extração dos dados.

### AWS Glue
 
Utilizo o Glue primeiramente para criar um data catalog com as duas tabelas dos arquivos raw (csv), essas duas tabelas são criadas a partir de um crawler com agendamento para rodar todo meio dia, esse crawler coleta os dados disponibilizados no bucket do s3 (spotify-dataops-raw).
Após isso utilizo o glue para rodar um script python com um ETL Job cujo objetivo é transformar os arquivos raw (csv) em refined (parquet) e deposita-los no bucket s3 (spotify-dataops-refined), por mais que não seja necessário, por não ser um grande volume de dados, o ponto disso é apenas testar e entender como funciona esse processo. Esse ETL também possui um agendamento, ele roda alguns minutos após o crawler que cria o data catalog raw rodar.
Para finalizar esse processo de transformação em parquet, temos um crawler que coleta dados refinados do S3 e criar um novo data catalog contendo as tabelas em formato parquet.

Para esse processo de transformação em parquet, utilizamos o seguinte código no ETL Job:

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

Com a criação dos DataCatalogs eu pude integrar o Athena a infraestrutura, possibilitando a escrita de SQL queries.

### AWS QuickSight

<h4 align="left"> 
:construction: QUICKSIGHT EM PLANEJAMENTO/ESTUDO :construction:
</h4>

## Instruções para execução

Para realizar a execução local desse código, é bem simples, primeiramente será necessário realizar a criação de um ambiente virtual python. Para isso existem diversas maneiras, porém, eu diria que a melhor seria utilizando o poetry.

O seguinte tutorial será para rodarmos o código de extração no clássico venv.

O primeiro passo é instalar o python, a versão que utilizei  é a 3.11, pois a mais recente na época não tinha todas as dependências necessárias para o projeto. 

Em seguida, iremos realizar a criação da nossa venv (Virtual Environment), podemos realizar isso com o seguinte comando:

python -m venv <nome-do-ambiente>

Esse comando irá criar o nosso ambiente na versão mais recente do python instalado na máquina local.

Com o ambiente criado, deveremos ter o seguinte parentesco do diretório:

```
> /[pasta-projeto]/
	> main.py (os outros .py são dedicados para utilização na AWS)
	> requirements.txt
	> <nome-da-venv>
	> <csvs-gerados>
```

Tendo isso, ou ao menos algo similar, precisamos ainda das bibliotecas. Para facilitar a instalação delas, criei um .txt utilizando o pip freeze contendo todas as libs da minha venv.

Para instalar será necessário estar no diretório do projeto, abrir o cmd e ativar o ambiente virtual, da seguinte maneira:

<venv>/Scripts/Activate.bat

e rodar o seguinte comando em seu terminal/cmd:

pip install -r requirements.txt

Após instalar todas as dependências/requisitos, será necessário ter em mãos o seu Client ID e Secret da API do Spotify e altera-los onde está marcado no código do script de extração <main.py>














## Planejamento do projeto e Autoria

Leonardo Martins - Analista de dados (Buscando experiência com arquitetura e engenharia de dados)
