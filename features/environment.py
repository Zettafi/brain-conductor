import os

from behave.runner import Context

from steps import selenium_steps, Config


def before_all(context: Context):
    try:
        context.config = Config(
            selenium_browser=os.getenv("SELENIUM_BROWSER", "chrome"),
            selenium_driver=os.getenv("SELENIUM_DRIVER", "local"),
            driver_location=os.getenv("SELENIUM_DRIVER_LOCATION", None),
            headless=os.getenv("SELENIUM_DRIVER_HEADLESS", "true").lower() == "true",
            selenium_server_uri=os.getenv(
                "SELENIUM_SERVER_URI", "http://localhost:4444/wd/hub"
            ),
            device_type=os.getenv("SELENIUM_DEVICE_TYPE", "desktop"),
            browser_wait_timeout=int(os.getenv("SELENIUM_BROWSER_WAIT_TIMEOUT", 60)),
            site_uri=os.environ["SITE_URI"],
        )
        selenium_steps.before_all(context)
    except KeyError as e:
        raise Exception(f"Missing environment variable: {e}")


def before_scenario(context: Context, scenario):
    selenium_steps.before_scenario(context, scenario)


def after_scenario(context: Context, scenario):
    selenium_steps.after_scenario(context, scenario)
