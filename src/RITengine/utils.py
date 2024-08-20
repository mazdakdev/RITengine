from datetime import timedelta

def parse_duration(duration_str):
    """ Convert a duration string to a timedelta object. """
    if duration_str.endswith('m'):
        return timedelta(minutes=int(duration_str[:-1]))
    elif duration_str.endswith('h'):
        return timedelta(hours=int(duration_str[:-1]))
    elif duration_str.endswith('d'):
        return timedelta(days=int(duration_str[:-1]))
    raise ValueError('Unsupported duration format')
