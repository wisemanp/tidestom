import requests
import numpy as np

from lasair import lasair_client
from tidestom.settings import BROKERS
lasair_ztf_token = BROKERS['LASAIR']['ztf_api_key']
lasair_ztf_url = "https://lasair-ztf.lsst.ac.uk"
lasair_lsst_token = BROKERS['LASAIR']['lsst_api_key']
lasair_lsst_url = "https://lasair-lsst.lsst.ac.uk"

##########
# Lasair #
##########
def is_site_up(url: str) -> bool:
    """Checks if a website is running.

    Parameters
    ----------
    url: website to check.
    
    Returns:
    --------
    bool: whether is up (True) or down (False)
    """
    try:
        response = requests.get(url, timeout=5)
        content = response.text.lower()

        # Look for maintenance / offline messages
        downtime_keywords = ["offline", "maintenance", "not available"]

        if response.status_code == 200:
            if any(word in content for word in downtime_keywords):
                print(f"{url} is DOWN ❌ (Maintenance page detected)")
                return False
            else:
                print(f"{url} is UP ✅ (Status: {response.status_code})")
                return True
        else:
            print(f"{url} is reachable but returned status {response.status_code} ⚠️")
            return False

    except requests.ConnectionError:
        print(f"{url} is DOWN ❌ (Connection error)")
        return False
    except requests.Timeout:
        print(f"{url} is DOWN ❌ (Timeout)")
        return False
    except requests.RequestException as e:
        print(f"{url} is DOWN ❌ (Error: {e})")
        return False
    
def find_target_name(ra: float, dec: float, survey: str) -> str | None:
    """Finds the nearest target from the given coordinates.

    The objects are queried from Lasair.

    Parameters
    ----------
    ra: Right ascension in degrees.
    dec: Declination in degrees.
    survey: Either "ztf" or "lsst".

    Returns
    -------
    target_name: Internal survey name or 'None' if not found.
    """
    assert survey in ["ztf", "lsst"], "Not a valid survey - either ztf or lsst"
    if survey == "ztf":
        url, token = lasair_ztf_url, lasair_ztf_token
    else:
        url, token = lasair_lsst_url, lasair_lsst_token
    # query objects
    if not is_site_up(url):
        return None
    lasair = lasair_client(token, endpoint = url + "/api")
    objects = lasair.cone(ra, dec)
    if len(objects) == 0:
        return None
    # get the object with the minimum separation
    if survey == "ztf":
        separations = [obj_dict['separation'] for obj_dict in objects]
        id_target = np.argmin(separations)
        target_name = objects[id_target]['object']
    else:
        # https://github.com/lsst-uk/lasair-examples/blob/main/notebooks/API_lsst/Cone_Search.ipynb
        object = objects['nearest']
        if 'object' in  object:
            target_name = object['object']
        else:
            return None
    return target_name