"""Administrator-maintained local estimator registry.

To add another trusted classifier, install its library in the application venv,
then edit this file ON THE ADMIN MACHINE. Never accept arbitrary Python plugins
from monitoring users or CSV files. Constructor signature must be (seed)->estimator.

Example (disabled by default):

  from sklearn.linear_model import LogisticRegression
  CUSTOM_ESTIMATORS = {
      'Logistic Regression': lambda seed: LogisticRegression(max_iter=800, random_state=seed)
  }
"""
CUSTOM_ESTIMATORS = {}
