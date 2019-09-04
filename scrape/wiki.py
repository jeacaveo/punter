""" Module for scraping prismata.gamepedia.com """
import requests


def get_content(url):
    """
    Get HTML for URL.

    Parameters
    ----------
    url : str
        Valid URL to get content for.

    Returns
    -------
    str
        HTML content.

    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    return ""
