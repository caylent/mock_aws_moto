help: ## Display help for this makefile
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

clean:
	rm -f .venv

setup_tests: ## Install poetry and then dependencies under its virtual environment
	@pip install poetry
	@poetry install
.PHONY: setup_tests

run_tests: ## Run tests
	@poetry run pytest .
.PHONY: run_tests

setup_invoke:  ## Install serverless to call lambdas locally
	@npm install -g serverless || echo "check https://www.serverless.com/framework/docs/getting-started"
.PHONY: setup_invoke

invoke_add_new_book: ## Run lambda locally
	@echo 'Add lambda input params. Example: {"attributes":{"author":"Some Name","title":"Some Title"},"file_path":"/home/michael/something"}'; \
	read PARAMS; \
	serverless invoke local --function  add_new_book --data="$${PARAMS}" --raw
.PHONY: invoke
