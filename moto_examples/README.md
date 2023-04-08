# Moto Examples

This repository was created as part of a Caylent's blog post to demonstrate the importance of testing your AWS calls, and use of moto this process.

To run the tests, run:
```
make setup_tests
make run_tests
```

To run the lambda locally you need to export the env vars, and then run
```
make setup_invoke  # In case you don't have serverless installed
make invoke_add_new_book params='{"book_attributes":{"author":"Some Name","title":"Some Title"},"file_path":"/path/of/your/file"}'
```