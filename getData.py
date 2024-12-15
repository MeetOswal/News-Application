from pyspark.sql import SparkSession
import os
os.environ['JAVA_HOME'] = 'C:/Program Files/Java/jdk-11.0.2'
os.environ['HADOOP_HOME'] = 'C:/hadoop'
os.environ['PYSPARK_PYTHON'] = 'C:/Users/oswme/anaconda3/envs/pyspark/python.exe'
os.environ['PYSPARK_DRIVER_PYTHON'] = 'C:/Users/oswme/anaconda3/envs/pyspark/python.exe'
spark = SparkSession.builder \
    .appName("SparkTest") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .getOrCreate()

# Create a simple DataFrame
data = [("Alice", 29), ("Bob", 31), ("Cathy", 25)]
columns = ["Name", "Age"]
df = spark.createDataFrame(data, columns)

# Show the DataFrame
df.show()
spark.stop()