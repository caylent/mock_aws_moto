"""Lambda handler and manager class of new book POST"""

import json
import os

import boto3


def run(event, context):
    """Method called by the lambda"""
    book_params = json.loads(event)
    new_book_manager = NewBookManager()
    new_book_manager.create_new_book(**book_params)
    return {'statusCode': 201, 'body': 'Your book was created'}


class NewBookManager:
    def __init__(self) -> None:
        self.books_bucket = os.environ['BOOKS_BUCKET']
        self.books_table = os.environ['BOOKS_TABLE']
        self.new_book_topic_arn = os.environ['NEW_BOOK_TOPIC_ARN']

        self.dynamodb_client = boto3.client('dynamodb')
        self.s3_client = boto3.client('s3')
        self.sns_client = boto3.client('sns')

    def create_new_book(self, attributes: dict, file_path: str) -> None:
        attributes['s3_key'] = f'books/{attributes["author"]}/{attributes["title"]}'
        self._create_book_instance(attributes)
        self._upload_book(s3_key=attributes['s3_key'], file_path=file_path)
        self._broadcast_new_book_message(attributes['author'], attributes['title'])

    def _create_book_instance(self, attributes: dict) -> None:
        self.dynamodb_client.put_item(
            TableName=self.books_table,
            Item={
                'Author': {'S': attributes['author']},
                'Title': {'S': attributes['title']},
                'Description': {'S': attributes.get('description')},
                'S3Key': {'S': attributes['s3_key']},
            }
        )

    def _upload_book(self, s3_key: str, file_path: str) -> None:
        self.s3_client.upload_file(Bucket=self.books_bucket, Key=s3_key, Filename=file_path)

    def _broadcast_new_book_message(self, author: str, title: str) -> None:
        self.sns_client.publish(
            TopicArn=self.new_book_topic_arn,
            Subject=f'A new book of {author}',
            Message=f'{title} was just published by {author}',
        )
