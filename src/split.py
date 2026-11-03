"""Time-based train / validation / test split for the loan default project."""

import pandas as pd

# Split boundaries (start dates are inclusive, end dates exclusive)
VALID_START = pd.Timestamp("2015-01-01")
TEST_START = pd.Timestamp("2015-07-01")


def split_by_date(df, date_column="issue_date"):
    """Split loans by issue date.

    Train:      issued before 2015-01-01        (2007-2014)
    Validation: issued 2015-01-01 to 2015-06-30 (Jan-Jun 2015)
    Test:       issued from 2015-07-01           (Jul-Dec 2015)
    """
    dates = df[date_column]

    train = df[dates < VALID_START]
    valid = df[(dates >= VALID_START) & (dates < TEST_START)]
    test = df[dates >= TEST_START]

    return train.copy(), valid.copy(), test.copy()