# Aldera

**Aldera** is a lightweight, framework-agnostic messaging toolkit providing a unified API for sending **email** and **SMS** messages. It supports both **Django** and **Flask**, and includes production-ready AWS backends using SES (email) and SNS (SMS).

Aldera is specifically designed for **AWS EC2 environments** using **IAM instance roles**.
No AWS keys should be hardcoded or stored in application configuration.

## Features
- **Framework-agnostic**: Works with Django and Flask; FastAPI support coming soon.
- **AWS-powered SMS delivery** via SNS.
- **Simple configuration** using your framework's native settings pattern.
- **Minimal code changes** needed to adopt across different frameworks.
- **Explicit backend selection** for predictable behavior.

## Installation

```bash
pip install aldera
```

To use asynchronous functionality, add `[async]` qualifier:

```bash
pip install aldera[async]
```

## Credential Philosophy

Aldera **does not accept** `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` settings.

Instead, Aldera relies entirely on the **standard AWS credential chain**, with the expectation that production deployments run on:
- EC2 instances with an **IAM role**
- ECS tasks with **task roles**
- Lambda execution roles
- Local development using AWS CLI profiles (optional)

This enforces best-practice AWS security and prevents accidental leakage of sensitive credentials.

## Flask Integration

### Flask SMS

```python
from flask import Flask
from aldera.sms.flask_sms import AlderaSMS
from aldera.sms import send_sms_message

aldera = AlderaSMS()

def create_app():
    app = Flask(__name__)
    app.config['ALDERA_SMS_BACKEND'] = 'aws'
    app.config['ALDERA_AWS_REGION'] = 'us-east-1'
    aldera.init_app(app)
    return app

@app.route("/test-sms")
def test_sms():
    send_sms_message("Hello from Flask!", "+15555555555")
    return "Message sent!"
```

#### Flask SMS config options

| Key |	Description |
|-----|-------------|
| `ALDERA_SMS_BACKEND` | `"aws"` or `"locmem"` |
| `ALDERA_AWS_REGION`	| AWS region for SNS |

No API keys needed — Aldera uses the EC2 instance role.

### Flask Email

```python
from flask import Flask
from aldera.mail.flask_mail import AlderaEmail, Message

mail = AlderaEmail()

def create_app():
    app = Flask(__name__)
    app.config['ALDERA_AWS_REGION'] = 'us-east-1'
    app.config['ALDERA_CONFIGURATION_SET'] = 'config-set'
    mail.init_app(app)
    return app

@app.route('/send')
def send_email():
    msg = Message(
        subject='Hello',
        recipients=['user@example.com'],
        body='This is a test email'
    )
    mail.send(msg)
    return 'Email sent!'
```

#### Flask email config options
| Key | Description |
| `ALDERA_AWS_REGION` | AWS SES region |
| `ALDERA_CONFIGURATION_SET` | Optional SES config set |

Again: **no AWS credentials needed.**


## Django Integration

### Django SMS Backend

Add Aldera to your installed apps:

```python
INSTALLED_APPS = [
    ...
    "aldera",
]
```

Configure the SMS system:

```python
ALDERA = {
    'SMS_BACKEND': 'aws',      # or "locmem"
    'AWS_REGION': 'us-east-1',
}
```

Send an SMS:

```python
from aldera.sms import send_sms_message

send_sms_message("Hello!", "+15555555555")
```

#### Credential note

No AWS keys required. Django code will automatically use the **EC2 instance role**.

### Django Email Backend (SES)

Use Aldera's AWS SES backend:

```python
EMAIL_BACKEND = "aldera.mail.backends.aws.AWSEmailBackend"
```

Configure the AWS region:

```python
ALDERA = {
    'AWS_REGION': 'us-east-1',
}
```

Then send email using Django’s built-in tools:

```python
from django.core.mail import send_mail

send_mail(
    "Subject",
    "Body",
    "from@example.com",
    ["to@example.com"],
)
```

## Why No AWS Keys?

Aldera is designed to run in environments where IAM roles are the correct security mechanism.
Hardcoding credentials is insecure, error-prone, and unnecessary.

Aldera follows AWS best practices by relying on:
- EC2 metadata credentials
- ECS task roles
- Lambda execution roles
- Optional AWS CLI profiles during local development

This makes migrations, deployments, and CI/CD pipelines safer and easier.

## Contributing

Pull requests are welcome!
If you'd like to add support for another framework or SMS backend, feel free to open an issue or PR.

## License

Aldera is released under an [Apache License 2.0](LICENSE).

## Author

Zack Young
