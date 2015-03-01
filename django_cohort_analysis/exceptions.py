"""Exceptions for Django Cohort Analysis"""


class NoMetricFileFound(Exception):
    """Raised when no metric file can be found by cohorts"""
    pass


class NoMetricFunctionsFound(Exception):
    """Raised when a metric file contains no functions"""
    pass


class InvalidUserModel(Exception):
    """Raised when an attempt to query the user model fails"""
    pass
