import pandas as pd
from src.loader import SlackDataLoader

def test_slack_loader_columns():
    # Initialize SlackDataLoader with a sample path
    slack_loader = SlackDataLoader("path/to/slack/data")

    # Get messages DataFrame
    messages_df = slack_loader.get_channel_messages("sample_channel")

    # Define expected columns
    expected_columns = ["column1", "column2", ...]  # Add the actual expected column names

    # Check if all expected columns are present in the DataFrame
    assert set(expected_columns).issubset(messages_df.columns), f"Columns mismatch. Expected: {expected_columns}, Actual: {messages_df.columns}"
