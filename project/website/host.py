from flask import request

def example_host():
    host = request.host
    return f"The host being used is: {host}"

host = example_host()