# Aldera SMS

**Aldera SMS** is a lightweight, framework-agnostic SMS delivery library designed to plug seamlessly into **Django**, **Flask**, and other Python uWSGI applications.

It provides a simple interface for sending SMS messages through AWS services such as SNS, while keeping your application code clean and portable.

Aldera SMS automatically detects the framework you are using (via explicit initialization) and exposes a consistent API for sending SMS messages.

# Features
- **Framework-agnostic**: Works with Django and Flask; FastAPI support coming soon.
- **AWS-powered SMS delivery** via SNS.
- **Simple configuration** using your framework's native settings pattern.
- **Minimal code changes** needed to adopt across different frameworks.
- **Explicit backend selection** for predictable behavior.

# Installation

```bash
pip install aldera
```

To use asynchronous functionality, add `[async]` qualifier:

```bash
pip install aldera[async]
```

# Configuration Guide

Aldera supports multiple Python web frameworks.
Configuration differs slightly depending on the framework.

## Django Integration

### 1. Add `aldera` to your installed apps

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    ...
    'aldera',
]
```

### 2. Add the required `ALDERA` settings

```python
ALDERA = {
    'SMS_BACKEND': 'aws',
    'AWS_REGION': 'us-east-1',
}
```

### 3. Sending an SMS

```python
from aldera.sms import send_sms_message

send_sms_message("Hello from Django!", "+15555555555")
```

Aldera automatically loads your Django settings from `django.conf.settings`.

## Flask Integration

Flask works differently from Django since configuration is stored on the `app.config` object.

### 1. Initialize the extension

```python
from flask import Flask
from aldera.flask_ext import Aldera
from aldera.sms import send_sms_message

aldera = Aldera()

def create_app():
    app = Flask(__name__)

    app.config.update({
        "ALDERA_SMS_BACKEND": "aws",
        "ALDERA_AWS_REGION": "us-east-1",
    })

    aldera.init_app(app)

    @app.route("/test-sms")
    def test_sms():
        send_sms_message("Hello from Flask!", "+15555555555")
        return "Message sent!"

    return app
```

Aldera retrieves settings directly from `app.config` when `init_app()` is called.

# API

#### `send_sms_message(message: str, phone_number: str)`

Sends an SMS using the configured backend.

Example:

```python
send_sms_message("Your code is 1234", "+15555555555")
```

# Environment Variables (Optional)

Aldera supports environment variable overrides:

| Variable | Description |
|---|---|
| `ALDERA_SMS_BACKEND` | Overrides backend selection |
| `ALDERA_AWS_REGION` | Overrides AWS region |

This allows flexible configuration across staging/production deployments.

# Backends

### AWS SNS (`aws`)

Primarily meant to be used on an EC2 instance. Requires the instance to have an IAM role with permission to publish messages via AWS Simple Notification Service.

### Asynchronous AWS SNS (`async_aws`)

Connects to AWS SNS using an asynchronous implementation of boto3. Also requires and IAM role with permission to publish messages via AWS SNS.

```python
from aldera.sms import send_async_message

async def send_code():
    await send_async_message("Hello from async!", "+15555555555")
```

### Local Memory (`locmem`)

Meant primarily for unit testing. Publishes messages to an attribute of the `sms` object.

```python
from aldera import sms
from aldera.sms import send_sms_message

send_sms_message("Hello unit tests!", "+15555555555")
print(len(sms.messages))                   # -> 1
print(sms.messages[0].message)             # -> "Hello unit tests!"
print(sms.messages[0].recipeint_number)    # -> "+15555555555"
```

# Contributing

Pull requests are welcome!
If you'd like to add support for another framework or SMS backend, feel free to open an issue or PR.

# License

Aldera is released under an [Apache License 2.0](LICENSE).

# Author

Zack Young
