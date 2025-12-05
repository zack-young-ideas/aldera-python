from aldera.sms.backends import async_aws, aws, locmem


backend_classes = {
    'async_aws': async_aws.AsyncSmsBackend,
    'aws': aws.SmsBackend,
    'locmem': locmem.SmsBackend,
}
