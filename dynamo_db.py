"""
based on https://aws.amazon.com/getting-started/guides/build-an-application-using-a-no-sql-key-value-data-store/module-one/
"""

import boto3

# boto3 is the AWS SDK library for Python.
# We can use the low-level client to make API calls to DynamoDB.
client = boto3.client('dynamodb')

try:
    resp = client.create_table(
        TableName="Books",
        # Declare your Primary Key in the KeySchema argument
        KeySchema=[
            {
                "AttributeName": "Author",
                "KeyType": "HASH"
            },
            {
                "AttributeName": "Title",
                "KeyType": "RANGE"
            }
        ],
        # Any attributes used in KeySchema or Indexes must be declared in AttributeDefinitions
        AttributeDefinitions=[
            {
                "AttributeName": "Author",
                "AttributeType": "S"
            },
            {
                "AttributeName": "Title",
                "AttributeType": "S"
            },
            {
                "AttributeName": "Description",
                "AttributeType": "S"
            },
            {
                "AttributeName": "S3Path",
                "AttributeType": "S"
            }
        ],
    )
    print("Table created successfully!")
except Exception as e:
    print("Error creating table:")
    print(e)


def get_books_instances(self, book_table: str, book_attributes: dict):
    filters = ' AND '.join([f"{key} = '{value}'" for key, value in book_attributes.items()])
    response = self.dynamodb_client.execute_statement(
        Statement=f'SELECT * FROM {book_table} WHERE {filters}'
    )
    return response['Items']
