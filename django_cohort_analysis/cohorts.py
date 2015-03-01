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

    :param datetime.datetime start_date: The date of creation of the earliest model instance
    :param datetime.datetime end_date: The date of creation of the newest model instance
    :param django.db.models.query.QuerySet queryset:  A list of model instances whos creation falls between the date range
    """
    def __init__(self, queryset, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.queryset = queryset


def snake_case_to_title(string):
    """ A convenience function that converts a snake-cased function name into title case

    :param str string: A string encoded using snake case
    :return: A converted string
    """
    return string.replace('_', ' ').title()


def get_file_or_default(metric_file):
    """ Returns the module name from which to extract metrics. Defaults to cohorts.metrics

    :param str metric_file:  The name of the module to extract metrics from
    :return: The name of the module where metric functions reside
    """
    return metric_file if metric_file is not None else 'cohorts.metrics'


def round_date_down(date_to_round):
    """Rounds a date down to the nearest Monday

    :param  datetime.datetime date_to_round:
    :return: The rounded down date
    :rtype: datetime.datetime
    """
    return date_to_round - timedelta(days=date_to_round.weekday())


def round_date_up(date_to_round):
    """Rounds a date up to the nearest Monday

    :param datetime.datetime date_to_round:
    :return: The rounded up date
    :rtype: datetime.datetime
    """
    return date_to_round - timedelta(days=(7 - date_to_round.weekday()))


def stretch_to_rounded_date_range(start_date, end_date):
    """Takes a date range and rounds the start date down and the end date up

    :param datetime.datetime start_date: The starting date
    :param  datetime.datetime end_date: The ending date
    :return: The rounded dates
    :rtype: tuple
    """
    rounded_start_date = round_date_down(start_date)
    rounded_end_date = round_date_up(end_date)
    return rounded_start_date, rounded_end_date


def get_sorted_metric_function_tuples(metrics_module):
    """Retrieves all metric functions from a file

    :param str metrics_module: The name of the module to retrieve metrics from
    :return: The name of the function and the function objects
    :rtype: tuple
    """
    return sorted(getmembers(metrics_module, isfunction))


def extract_instances_in_date_range(model_instances, time_window_start, time_window_end):
    """Retrivies all instances of a model within a given time window

    :param django.db.models.query.QuerySet model_instances: The model to filter again
    :param  datetime.datetime time_window_start:
    :param  datetime.datetime time_window_end:
    :return: A queryset containing model instances in the date range
    :rtype: django.db.models.query.QuerySet
    """
    if model_instances.model.__name__ == 'User':
        return model_instances.filter(date_joined__ranged=(time_window_start, time_window_end))
    else:
        return model_instances.filter(date_created__range=(time_window_start, time_window_end))


def get_time_window_from_date(date, window_length=6):
    """ Takes a starting date and calculates a date range from it

    :param datetime.datetime date: The starting date
    :param int window_length: The number of days to calculate against
    :return: starting_date, ending_date
    :rtype: tuple
    """
    end_date = date + timedelta(days=window_length)
    return date, end_date


def get_cohorts_from_model(model, start_date, end_date):
    """Retrieves a list of cohorts from a given Django model

    :param django.db.models.Model model: The model class to filter from
    :param datetime.datetime start_date:
    :param datetime.datetime end_date:
    :return: A list of cohorts
    :rtype: Cohort
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

    :param str metric_file: The name of the file to look in
    :return: Tuples containing (function name, function object)
    :rtype: list
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

    :param datetime.datetime date:
    :rtype: int
    """
    return date.isocalendar()[1]


def create_default_dict_for_cohort(cohort):
    """Creates an empty dictionary for cohort analysis

    :param Cohort cohort: The cohort to create a dictionary for
    :return: A dictionary containing the analysis and born_week keys
    :rtype: OrderedDict
    """
    default_dict = OrderedDict()
    default_dict['born_week'] = get_isoweek_from_date(cohort.start_date)
    default_dict['analysis'] = []
    return default_dict


def map_metric_to_cohort(metric, cohort, start_date, end_date):
    """Applies a metric function to a cohort

    :param  tuple metric: Must contain (function name, function object)
    :param Cohort cohort:
    :param datetime.datetime start_date:
    :param datetime.datetime end_date:
    :return: A dict containing a formated function name and the result of the metric function_name
    :rtype: OrderedDict
    """
    metric_analysis = OrderedDict()
    metric_analysis['function_name'] = snake_case_to_title(metric[0])
    metric_analysis['analysis_result'] = metric[1](cohort, cohort.start_date, end_date)
    return metric_analysis


def analyze_cohorts(cohorts, metric_file, start_date, end_date):
    """Apply analysis to a list of cohorts

    :param list cohorts: A list of Cohort objects
    :param str metric_file: The name of the file where the metrics live
    :param datetime.datetime start_date:
    :param datetime.datetime end_date:
    :return: A list of analysis dictionaries, one for each cohort
    :rtype: list
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

    :param django.db.models.Model model: A model to apply metrics to
    :param datetime.datetime start_date:
    :param datetime.datetime end_date:
    :param str metric_file: The name of the metric file to pull from
    :return: A list of analysis dictionaries for each cohorts
    :rtype: list
    """
    rounded_start_date, rounded_end_date = stretch_to_rounded_date_range(start_date, end_date)
    metric_file = get_file_or_default(metric_file)
    cohorts = get_cohorts_from_model(model, rounded_start_date, rounded_end_date)
    analysis = analyze_cohorts(cohorts, metric_file, rounded_start_date, rounded_end_date)
    return analysis


def analysis_to_json(analysis):
    """Convenience method to convert an analysis list to a JSON file"""
    return json.dumps(analysis)
