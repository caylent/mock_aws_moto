import os
from typing import List

import boto3


class BookManager:

    def __init__(self) -> None:
        self.books_bucket = os.environ['BOOKS_BUCKET']
        self.books_table = os.environ['BOOKS_TABLE']
        self.new_book_topic_arn = os.environ['NEW_BOOK_TOPIC_ARN']
        self.recommendation_source_email = os.environ['RECOMMENDATION_SOURCE_EMAIL']

        self.dynamodb_client = boto3.client('dynamodb')
        self.s3_client = boto3.client('s3')
        self.sns_client = boto3.client('sns')
        self.sqs_client = boto3.client('sqs')
        self.ses_client = boto3.client('ses')

    def create_new_book(self, book_attributes: dict, file_path: str) -> None:
        book_attributes['S3Path'] = f'books/{book_attributes["Author"]}/{book_attributes["Title"]}'
        self._create_book_instance(book_attributes)
        self._upload_book(s3_key=book_attributes['S3Path'], file_path=file_path)
        self.s3_client.upload_file(
            Bucket=self.books_bucket,
            Key=book_attributes['S3Path'],
            Filename=file_path,
        )
        self._broadcast_new_book_message(book_attributes['Author'], book_attributes['Title'])

    def _create_book_instance(self, book_attributes: dict) -> None:
        self.dynamodb_client.put_item(
            TableName=self.books_table,
            Item={
                'Author': {
                    'S': book_attributes['Author'],
                },
                'Title': {
                    'S': book_attributes['Title'],
                },
                'Description': {
                    'S': book_attributes.get('Description'),
                },
                'S3Path': {
                    'S': book_attributes['S3Path'],
                },
            }
        )

    def _upload_book(self, s3_key: str, file_path: str) ->:
        self.s3_client.upload_file(
            Bucket=self.books_bucket,
            Key=s3_key,
            Filename=file_path,
        )

    def _broadcast_new_book_message(self, author: str, title: str) -> None:
        self.sns_client.publish(
            TopicArn=self.new_book_topic_arn,
            Subject=f'A new book of {author}',
            Message=f'{title} was just published by {author}',
        )

    def send_user_recommendation(self, user_name: str, author: str, title: str, emails: List[str]) -> None:
        book_instance = self._get_book_instance(author, title)
        self.ses_client.send_email(
            Source=self.recommendation_source_email,
            Destination={
                'ToAddresses': emails,
            },
            Message={
                'Subject': {
                    'Data': f'{user_name} has a suggestion for you'
                },
                'Body': {
                    'Text': {
                        'Data': (
                            f'Your friend {user_name} sends a recommendation: '
                            f'check {title} from {author}! \n {book_instance["Description"]}'),
                    },
                }
            }
        )

    def _get_book_instance(self, author: str, title: str):
        response = self.dynamodb_client.get_item(
            TableName=self.books_table,
            Key={
                'Author': {'S': author},
                'Title': {'S': title},
            }
        )
        return response['Item']
