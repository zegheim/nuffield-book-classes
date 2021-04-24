# nuffield-book-classes

This is a command line tool to book swimming slots in Nuffield Health programmatically.

# Prerequisites

This repo uses [`pipenv`](https://pypi.org/project/pipenv/) to manage its dependencies. For a complete list of dependencies please look at `Pipfile`.

# Installation

1. Clone this repo.
2. `cd` into the repo, and run `pipenv install`.
3. Copy `config.py.example` to `config.py`, and fill in as needed.

# Usage

This tool accepts the following positional / optional arguments:

## Positional
- `START_TIME`: Desired slot start time, in HHMM format (e.g. 8AM -> 800, 7PM -> 1900, etc.)

## Optional
- `-l` / `--lane`: Desired lane to swim in. One of `SLOW`, `MEDIUM`, or `FAST`. Default = `MEDIUM`.
- `-d` / `--days-ahead`: How many days forward to book for. Default = 8.

# Disclaimer
This tool is provided "as is" - by using this tool you agree that I am not responsible for any loss arising due to this tool.
