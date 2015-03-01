"""The main module for all cohort related functions
"""
from inspect import getmembers, isfunction
from importlib import import_module
try:
    from collections import OrderedDict
except ImportError:
    # Python < 2.7
    from ordereddict import OrderedDict
import json
from datetime import timedelta
from exceptions import (NoMetricFileFound,
                        NoMetricFunctionsFound,
                        InvalidUserModel)


class Cohort:
    """A wrapper class for cohorts

    Attributes:
        start_date (datetime.datetime): The date of creation of the earliest model instance
        end_date (datetime.datetime): The date of creation of the newest model instance
        queryset (django.db.models.query.QuerySet): A list of model instances whos creation falls between the date range
    """
    def __init__(self, queryset, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.queryset = queryset


def snake_case_to_title(string):
    """ A convenience function that converts a snake-cased function name into title case
    Args:
        string (str): A string encoded using snake case
    Returns:
        retval (str): A converted string
    """
    return string.replace('_', ' ').title()


def get_file_or_default(metric_file):
    """ Returns the module name from which to extract metrics. Defaults to cohorts.metrics
    Args:
        metric_file (str): The name of the module to extract metrics from
    Returns:
        retval (str): The name of the module where metric functions reside
    """
    return metric_file if metric_file is not None else 'cohorts.metrics'


def round_date_down(date_to_round):
    """Rounds a date down to the nearest Monday
    Args:
        date_to_round (datetime.datetime):
    Returns:
        retval (datetime.datetime): The rounded down date
    """
    return date_to_round - timedelta(days=date_to_round.weekday())


def round_date_up(date_to_round):
    """Rounds a date up to the nearest Monday
    Args:
        date_to_round (datetime.datetime):
    Returns:
        retval (datetime.datetime): The rounded up date
    """
    return date_to_round - timedelta(days=(7 - date_to_round.weekday()))


def stretch_to_rounded_date_range(start_date, end_date):
    """Takes a date range and rounds the start date down and the end date up
    Args:
        start_date (datetime.datetime): The starting date
        end_date (datetime.datetime): The ending date
    Returns:
        retval (tuple): Contains the new rounded dates
    """
    rounded_start_date = round_date_down(start_date)
    rounded_end_date = round_date_up(end_date)
    return rounded_start_date, rounded_end_date


def get_sorted_metric_function_tuples(metrics_module):
    """Retrieves all metric functions from a file
    Args:
        metrics_module (str): The name of the module to retrieve metrics from
    Returns:
        retval (tuple): Contains (name of function, function object)
    """
    return sorted(getmembers(metrics_module, isfunction))


def extract_instances_in_date_range(model_instances, time_window_start, time_window_end):
    """Retrivies all instances of a model within a given time window
    Args:
        model_instances (django.db.models.query.QuerySet): The model to filter again
        time_window_start (datetime.datetime):
        time_window_end (datetime.datetime):
    Returns:
        retval (django.db.models.query.QuerySet): A queryset containing model instances in the date range
    """
    return model_instances.filter(date_created__range=(time_window_start, time_window_end))


def get_time_window_from_date(date, window_length=6):
    """ Takes a starting date and calculates a date range from it
    Args:
        date (datetime.datetime): The starting date
        window_length (int): The number of days to calculate against
    Returns:
        retval (tuple): Contains (starting_date, ending_date)
    """
    end_date = date + timedelta(days=window_length)
    return date, end_date


def get_cohorts_from_model(model, start_date, end_date):
    """Retrieves a list of cohorts from a given Django model
    Args:
        model (django.db.models.Model): The model class to filter from
        start_date (datetime.datetime):
        end_date (datetime.datetime):
    Returns:
        cohorts (list of Cohort):
    """
    cohorts = []
    try:
        time_window_start, time_window_end = get_time_window_from_date(start_date)
        all_model_instances = model.objects.all()
        while time_window_end < end_date:
            instances_in_window = extract_instances_in_date_range(all_model_instances, time_window_start,
                                                                  time_window_end)
            cohorts.append(Cohort(instances_in_window, time_window_start, time_window_end))
            time_window_start += timedelta(weeks=1)
            time_window_end += timedelta(weeks=1)
    except model.DoesNotExist:
        raise InvalidUserModel
    return cohorts


def get_metrics_from_file(metric_file):
    """Gets all metric functions within a file
    Args:
        metric_file (str): The name of the file to look in
    Returns:
        metrics (list of tuple): A list of tuples containing (function name, function object)
    """
    try:
        metrics = import_module(metric_file)
        metrics = get_sorted_metric_function_tuples(metrics)
    except ImportError:
        raise NoMetricFileFound
    if not metrics:
        raise NoMetricFunctionsFound
    return metrics


def get_isoweek_from_date(date):
    """Convenience method to get the ISO week from a datetime
    Args:
        date (datetime.datetime):
    Returns:
        retval (int):
    """
    return date.isocalendar()[1]


def create_default_dict_for_cohort(cohort):
    """Creates an empty dictionary for cohort analysis
    Args:
        cohort (Cohort): The cohort to create a dictionary for
    Returns:
        retval (OrderedDict): A dictionary containing the analysis and born_week keys
    """
    default_dict = OrderedDict()
    default_dict['born_week'] = get_isoweek_from_date(cohort.start_date)
    default_dict['analysis'] = []
    return default_dict


def map_metric_to_cohort(metric, cohort, start_date, end_date):
    """Applies a metric function to a cohort
    Args:
        metric (tuple): Must contain (function name, function object)
        cohort (Cohort):
        start_date (datetime.datetime):
        end_date (datetime.datetime):
    Returns:
        metric_analysis (OrderedDict): A dict containing a formated function name and the result of the metric function_name
    """
    metric_analysis = OrderedDict()
    metric_analysis['function_name'] = snake_case_to_title(metric[0])
    metric_analysis['analysis_result'] = metric[1](cohort, cohort.start_date, end_date)
    return metric_analysis


def analyze_cohorts(cohorts, metric_file, start_date, end_date):
    """Apply analysis to a list of cohorts
    Args:
        cohorts (list of Cohort): A list of Cohort objects
        metrics_file (str): The name of the file where the metrics live
        start_date (datetime.datetime):
        end_date (datetime.datetime):
    Returns:
        analysis (list of dict): A list of analysis dictionaries, one for each cohort
    """
    analysis = []
    metrics = get_metrics_from_file(metric_file)
    for cohort in cohorts:
        cohort_analysis_dict = create_default_dict_for_cohort(cohort)
        for metric in metrics:
            metric_analysis = map_metric_to_cohort(metric, cohort, start_date, end_date)
            cohort_analysis_dict['analysis'].append(metric_analysis)
        analysis.append(cohort_analysis_dict)
    return analysis


def analyze_cohorts_for_model(model, start_date, end_date, metric_file=None):
    """Retrives a model and applies cohort analysis to it
    Args:
        model (django.db.models.Model): A model to apply metrics to
        start_date (datetime.datetime):
        end_date (datetime.datetime):
        metric_file (str, optional): The name of the metric file to pull from
    Returns:
        analysis (list of dict): A list of analysis dictionaries for each cohorts
    """
    rounded_start_date, rounded_end_date = stretch_to_rounded_date_range(start_date, end_date)
    metric_file = get_file_or_default(metric_file)
    cohorts = get_cohorts_from_model(model, rounded_start_date, rounded_end_date)
    analysis = analyze_cohorts(cohorts, metric_file, rounded_start_date, rounded_end_date)
    return analysis


def analysis_to_json(analysis):
    """Convenience method to convert an analysis list to a JSON file"""
    return json.dumps(analysis)
