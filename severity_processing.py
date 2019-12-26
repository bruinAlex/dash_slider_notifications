import pandas as pd
import numpy as np
from datetime import timedelta, date, datetime
import collections


def trailing_days_df(df, date, trailing_days=3):
	"""
	Return a sliced dataframe starting and t=0 and going backwards n days.
	Date should be a string with yyyy-mm-dd format
	"""
	current_index = df.loc[df['date'] == date].index[0]
	first_day_idx = max(0, current_index - trailing_days)
	return df.iloc[first_day_idx:current_index+1, :].copy()


def p0_severity(df):
	"""
	Returns a critical warning if it exists for test date
	"""
	recent_value = df.problem_0.values[-1]
	if recent_value:
		return 'Critical'
	else:
		return None


def p1_severity(df):
	"""
	Return the severity based on time
	"""
	# Take the sliced df and put problem_1 values in reverse time order from most recent to oldest
	reversed_values = df.problem_1.values[::-1]
	
	if reversed_values[0] == 1: # If test date is 1
		num_consecutive_days = 0
		for value in reversed_values:
			if value == 0:
				break
			else:
				num_consecutive_days += value
	else:
		return (None, None)
	
	# Severity mapping
	severity_dict = {
		1: 'Low',
		2: 'Moderate',
		3: 'High',
		4: 'Critical'
	}
	
	severity_level = severity_dict[num_consecutive_days]
	
	return severity_level, num_consecutive_days


def p2_severity(df):
	"""
	Returns severity based on number
	"""
	recent_value = df.problem_2.values[-1]
	
	if (recent_value > 0) & (recent_value <= 3):
		return 'Low', recent_value
	elif (recent_value > 3) & (recent_value <= 6):
		return 'Moderate', recent_value
	elif (recent_value > 6) & (recent_value <= 9):
		return 'High', recent_value
	elif (recent_value > 9) :
		return 'Critical', recent_value
	else:
		return (None, None)
	

def categorized_error_dict(df):
	"""
	Take in pre-sliced list and return a dict of warnings by classification
	"""
	categorized_error_dict = collections.defaultdict(list)
	
	p0_severity_level = p0_severity(df)
	p1_severity_level, num_consecutive_days = p1_severity(df)
	p2_severity_level, count = p2_severity(df)
	
	if p0_severity_level:
		categorized_error_dict[p0_severity_level].append("server_0 has problem_0 status")
	if p1_severity_level:
		categorized_error_dict[p1_severity_level].append(f"server_0 has had problem_1 status for {num_consecutive_days} day(s)")
	if p2_severity_level:
		categorized_error_dict[p2_severity_level].append(f"server_0 has {count} report(s) of problem_2 status")
	
	return categorized_error_dict