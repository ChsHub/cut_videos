from datetime import datetime
from os.path import splitext
from re import findall

strptime = datetime.strptime
time_format = '%H:%M:%S.%f'
zero_time = '00:00:00.000'

def unformat_time(time: str) -> str:
    """
    Convert stort time string to long form (digits only)
    :param time: Short time string
    :return: Long format time 8 digit string
    """
    if '.' in time:
        time, milli = time.split('.')
        milli += (2 - len(milli)) * '0'  # Add trailing zeroes
    else:
        milli = '00'

    # Add redundant zeroes
    time = time.split('-')
    while len(time) < 3:
        time = ['00'] + time
    for i, t in enumerate(time):
        time[i] = (2 - len(t)) * '0' + t

    return ''.join(time) + milli


def format_time(time: str) -> str:
    """
    Format time to shortened human readable form
    :param time: Time string in long form
    :return: Time string in shortened form
    """
    time, milli = splitext(time)
    time = findall(r'([1-9]\d?)|00', time)
    time = '-'.join(time)
    time = time.lstrip('-')
    milli = milli.rstrip('0')
    milli = milli.rstrip('.')
    return time + milli