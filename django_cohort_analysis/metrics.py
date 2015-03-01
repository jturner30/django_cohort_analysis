"""Metrics

All metrics in this file are called by cohorts.analyze_cohorts_for_model and follow the format:
function_name(cohort, start_date, end_date)

"""
from datetime import timedelta


def example_metric(cohort, start_date, end_date):
    """An example metric that returns the number of members in a queryset

    Args:
        cohort (cohorts.Cohort): The cohort to analyze
        start_date (datetime.datetime): The lower bounds of the date range to analyze
        end_date (datetime.datetime): The upper bounds of the date range to analyze

    Returns:
        list: A list of metric results to be added to the analysis dictionary
    """
    result = []
    window_start_date = start_date
    window_end_date = window_start_date + timedelta(weeks=1)
    while window_end_date < end_date:
        result.append(cohort.queryset.count())
        window_start_date += window_end_date + timedelta(days=1)
        window_end_date += window_start_date + timedelta(weeks=1)
    return result
