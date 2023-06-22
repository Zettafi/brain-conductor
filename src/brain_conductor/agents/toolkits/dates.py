"""Date toolkit module"""
from datetime import datetime


class Dates:
    """
    Dates toolkit
    """

    @staticmethod
    async def get_current_date():
        """
        Get the current date
        :return: A textual representation for use by LLMs in completion requests
        """
        now = datetime.now().strftime("%d %B, %Y")
        return f"The current date is: {now}"
