# Mocking AWS calls using moto (python)

## Introduction - Tests Overview

### ADD SOME EXAMPLES in this section: online book store

Tests are important, everyone knows that. Increasing reliability; preventing further changes from affecting the code's current behavior; allowing to test beforehand several scenarios. If implemented correctly tests also allow the insertion of new test cases easily, fixing possible or actual bugs, and preventing they to happen again in the future.

The application can be tested in several levels, receiving different names depending on the goal of the test. There are the end-to-end (E2E) tests, integration tests, unit tests, etc. The short description of the three I cited would be:

- *E2E*: test a entire flow of the application. Handle the system as a black box: giving some input checks the output. Usually tested against alpha environment.
- *Integration*: test parts of the flow, focusing on the integration with other services (owned or 3rd parties), ensuring that all the external calls are working properly. Usually use services' sandbox and/or alpha environment (if you mock the calls, you won't be testing the integration)
- *Unit*: as the name indicates, it tests the smallest piece of a code, the methods. It checks if all intermediate steps are working as they were developed for. It is used locally and on CI/CD pipelines, blocking the most common bugs known from being merged into the code.

Another characteristic of unit tests is the use of mock. Mocking external calls is a strategy used when we don't want to make requests (specially the paid ones) all the time. It make your test faster, cheaper, and allow you to simulate behaviors that would be very difficult (or even impossible) to reproduce making the real call.

The goal of unit tests is to check if the methods will work with given input and expected request responses, and it should be your most frequent test, running locally before a git push and remotely before any merge into the main code.


## Mocking

Mock in software development is the idea of overwriting some piece of code with other piece of code during run time, almost saying "when the code reaches this part, do this other thing instead". Imagine our book platform once again, once a user submits an order, a `check_credit_card` method must be call to know if the card is valid. That check having a cost pushes us to avoid calling it on every test of this part of the code during the development, specially if those tests runs very frequently, as unit tests usually do. But, we can still run this code as it is, if we fake that credit card check request during run time, returning the expected response.

While mocking is a good approach on unit tests, there are many ways to do it. Mocking an entire library, a method like `check_credit_card`, or a request inside a method `requests.post(url='https://wanted_api.com/post/')`, and the closer your are from mocking a request or single line of your code the better, meaning all your logic is being run on your test.

### Mocking AWS services

Overwriting directly AWS's SDK client or a client's method to intercept the aws request and fake the response would work, but may not be best way to handle that. It is hard to cover all possible behaviors and errors that can happen doing that manually. Even if you could do, would you keep that up to date as the SKD updates ? Mocking AWS services can be complicated without the right tools.

On that context, there are tools that reproduce AWS services behavior, or at least most service's behavior, and they can behave differently. Many of the solutions are very small and cover only one or two services. But, we also have others that covers many services, like [localstack](https://localstack.cloud/) and [moto](http://docs.getmoto.org/en/latest/index.html).

Localstack creates a server to emulates several AWS services. Therefore, updating your endpoint-url to this server you can redirect your [AWS CLI](https://aws.amazon.com/cli/) or any language (through [AWS SDKs](https://aws.amazon.com/developer/tools/)) to develop and test locally, offline. Localstack has a docker image ready to use, and works greatly with docker compose, in case you want to run yours or a third party application, even a database on other docker instances.

Moto is a python library that can work as localstack, using it's [server mode](http://docs.getmoto.org/en/latest/docs/server_mode.html), allowing to be used with other languages (other SDKs). In addition, moto can also run without the server mode, being executed as python code. This is particularly interesting when developing python unit tests, avoiding the need of configuring your CI/CD to run a server to begin testing.

### Moto hands-on

Now, let's analyze some code. Keep in mind that the code shown is very naive, focused on demonstrating how to mock AWS services and test your code. No expecption are considered here, what means that changing the parameter is a great way to discover what could happen in advance.

Consider our online bookstore once again. Imagine that an author wants to register a new book on the platform. On the backend, our lambda needs to get the book information, save it in the database (here we will be using a DynamoDB), upload the book file to S3, and save its S3 key to find the book later just with a database query. After uploading we want to send an SNS message, broadcasting this new book arrival, to send automatic emails to subscribers, or to use the fanout pattern, sending it to SQS queues for other purposes.

Look this naive code that could be called by a lambda's handler:
```python
class BookManager:
    def __init__(self) -> None:
        self.books_bucket = os.environ['BOOKS_BUCKET']
        self.books_table = os.environ['BOOKS_TABLE']
        self.dynamodb_client = boto3.client('dynamodb')
        self.s3_client = boto3.client('s3')
        self.sns_client = boto3.client('sns')

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
```

Very simple code: a lambda, running a manager that calls 3 AWS services, no big deal, now let's test it with pytest.

```python
def test_creating_new_book(main_fixture):
    """Create a new book, using dynamoDB, S3 and SNS services"""

    author = 'George R. R. Martin'
    title = 'A Song of Ice and Fire'
    book_attributes = {
        'Author': author,
        'Title': title,
        'Description': 'A good book',
    }

    BookManager().create_new_book(book_attributes, main_fixture.data_path/'book_example.pdf')

    main_fixture.assert_dynamo_item(author=author, title=title)
    main_fixture.assert_s3_object(
        key='books/George R. R. Martin/A Song of Ice and Fire',
        expected_text='This is a book'
    )
    main_fixture.assert_new_book_message_sent(
        expected_message=f'{title} was just published by {author}'
    )
```

Also very simple, right ? Input, call the method and 3 asserts, one for each service, to check if it did what it supposed to do. The whole logic is actually inside the `main_fixture`, let's have a look before more comments on that.


```
def set_mocked_aws_credentials():
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
```

Then, we need to create our mocked bucket, in order to access it:
```
def
```
