"""
All metrics in this file are called by cohorts.analyze_cohorts_for_model and follow the format:
function_name(cohort, start_date, end_date)
"""
from datetime import timedelta


def example_metric(cohort, start_date, end_date):
    """An example metric that returns the number of members in a queryset

    :param cohorts.Cohort cohort: The cohort to analyze
    :param datetime.datetime start_date: The lower bounds of the date range to analyze
    :param datetime.datetime end_date: The upper bounds of the date range to analyze
    :return: A list of metric results to be added to the analysis dictionary
    """
    result = []
    window_start_date = start_date
    window_end_date = window_start_date + timedelta(weeks=1)
    while window_end_date < end_date:
        result.append(cohort.queryset.count())
        window_start_date += window_end_date + timedelta(days=1)
        window_end_date += window_start_date + timedelta(weeks=1)
    return result
