from pyspark.sql import SparkSession

from pydeequ.checks import Check, CheckLevel
from pydeequ.verification import VerificationSuite


spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("Project029-Deequ-Test")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")


data = [
    ("CUST_001", "ACTIVE", 1000.0),
    ("CUST_002", "ACTIVE", 2500.0),
    ("CUST_003", "CLOSED", 500.0),
    ("CUST_004", "ACTIVE", 750.0),
]

df = spark.createDataFrame(
    data,
    ["CustomerID", "Status", "Amount"]
)

print("\nDataset:")
df.show()

check = (
    Check(spark, CheckLevel.Error, "Basic Data Quality Checks")
    .hasSize(lambda x: x == 4)
    .isComplete("CustomerID")
    .isUnique("CustomerID")
    .isComplete("Status")
    .isComplete("Amount")
    .isNonNegative("Amount")
)

result = VerificationSuite(spark).onData(df).addCheck(check).run()

result_df = result.checkResultsAsDataFrame(spark)

print("\nDeequ Results:")
result_df.show(truncate=False)

spark.stop()

print("\nDeequ test completed.")