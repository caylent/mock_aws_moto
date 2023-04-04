import os
from contextlib import ExitStack
from functools import cached_property
from pathlib import Path
from unittest.mock import patch

import boto3
import moto
import pytest
from moto.core import DEFAULT_ACCOUNT_ID
from moto import mock_dynamodb, mock_s3, mock_ses, mock_sns


MOCKED_ENV_VARS = {
    'BOOKS_BUCKET': 'books_bucket',
    'BOOKS_TABLE': 'Books',
    'NEW_BOOK_TOPIC': 'new-book-topic',
    'RECOMMENDATION_SOURCE_EMAIL': 'book_recommendator@caylent.com',
}


class MainFixture():
    def __init__(self):
        self.data_path = Path(__file__).parent / "resources"
        self.env_vars = MOCKED_ENV_VARS
        self.dynamodb_client = boto3.client('dynamodb')
        self.s3_client = boto3.client('s3')
        self.sns_client = boto3.client('sns')
        self.ses_client = boto3.client('ses')

        self.sns_backend = moto.sns.sns_backends[DEFAULT_ACCOUNT_ID]["us-east-1"]

    def setup(self) -> ExitStack:
        exit_stack = ExitStack()
        exit_stack.enter_context(patch.dict(os.environ, MOCKED_ENV_VARS))
        self.create_books_table()
        self.create_books_bucket()
        self.verify_email()
        self.new_book_topic_arn  # Ensure new book topic is created
        return exit_stack

    def add_book(self, author, title):
        self.dynamodb_client.put_item(
            TableName=self.env_vars['BOOKS_TABLE'],
            Item={
                'Author': {
                    'S': author,
                },
                'Title': {
                    'S': title,
                },
                'Description': {
                    'S': 'A test description',
                }
            }
        )

    def create_books_bucket(self) -> None:
        self.s3_client.create_bucket(Bucket=self.env_vars['BOOKS_BUCKET'])

    def create_books_table(self) -> None:
        self.dynamodb_client.create_table(
            TableName=self.env_vars['BOOKS_TABLE'],
            KeySchema=[
                {"AttributeName": "Author", "KeyType": "HASH"},
                {"AttributeName": "Title", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "Author", "AttributeType": "S"},
                {"AttributeName": "Title", "AttributeType": "S"},
            ],
            BillingMode='PAY_PER_REQUEST',
        )

    @cached_property
    def new_book_topic_arn(self) -> str:
        topic_arn = self.sns_client.create_topic(Name=self.env_vars['NEW_BOOK_TOPIC'])['TopicArn']
        os.environ['NEW_BOOK_TOPIC_ARN'] = topic_arn
        return topic_arn

    def s3_upload_file(self, bucket, s3_key: str, file_name=None) -> None:
        """Upload file on resources/common to s3 - with the same file name by default"""
        file_name = file_name or s3_key
        bucket.upload_file(Filename=str(self.data_path/file_name), Key=s3_key)

    def verify_email(self) -> None:
        self.ses_client.verify_email_address(EmailAddress=self.env_vars['RECOMMENDATION_SOURCE_EMAIL'])

    def assert_s3_object(self, key, expected_text) -> None:
        response = self.s3_client.get_object(Bucket=self.env_vars['BOOKS_BUCKET'], Key=key)
        object_body = response['Body'].read().decode('utf-8')
        assert expected_text in object_body

    def assert_dynamo_item(self, author, title) -> None:
        response = self.dynamodb_client.get_item(
            TableName=self.env_vars['BOOKS_TABLE'],
            Key={
                'Author': {'S': author},
                'Title': {'S': title},
            }
        )
        assert response.get('Item')

    def assert_new_book_message_sent(self, expected_message: str) -> None:
        sent_notifications = self.sns_backend.topics[self.new_book_topic_arn].sent_notifications
        sns_message_value = sent_notifications[0][1]
        assert expected_message in sns_message_value


@pytest.fixture
def main_fixture():
    set_mocked_aws_credentials()

    with mock_dynamodb(), mock_s3(), mock_sns(), mock_ses():
        fixture = MainFixture()
        with fixture.setup():
            yield fixture


def set_mocked_aws_credentials():
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
