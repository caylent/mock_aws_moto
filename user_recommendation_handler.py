"""Lambda handler and manager class of user's recommendation flow"""

import json
import os
from typing import List

import boto3


def run(event, context):
    """Method called by the lambda"""
    book_params = json.loads(event)
    manager = UserRecommendationManager()
    manager.send_user_recommendation(**book_params)
    return {'statusCode': 201, 'body': 'Your recommendation was sent'}


class UserRecommendationManager:

    def __init__(self) -> None:
        self.books_table = os.environ['BOOKS_TABLE']
        self.recommendation_source_email = os.environ['RECOMMENDATION_SOURCE_EMAIL']
        self.dynamodb_client = boto3.client('dynamodb')
        self.ses_client = boto3.client('ses')

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
