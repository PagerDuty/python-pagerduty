from setuptools import setup

__version__ = '1.0.0'

if __name__ == '__main__':
    setup(
        name='pagerduty',
        description="python-pagerduty",
        long_description="Clients for PagerDuty's APIs",
        py_modules=['pagerduty'],
        version=__version__,
        license='MIT',
        url='https://pagerduty.github.io/python-pagerduty',
        download_url='https://pypi.org/project/pagerduty/',
        install_requires=['certifi', 'requests', 'urllib3'],
        author='PagerDuty',
        author_email='support@pagerduty.com',
        python_requires='>=3.6'
    )
