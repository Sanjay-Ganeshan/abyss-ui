import browser_cookie3
import os

domain = "https://act.hoyolab.com"

def find_cookie_files():
    parent_dir = "C:\\Users\\sanga\\AppData\\Local\\Google\\Chrome\\User Data"
    for (root, subdirs, subfiles) in os.walk(parent_dir):
        for each_file in subfiles:
            abs_file = os.path.join(parent_dir, root, each_file)
            if each_file == "Cookies" or each_file == "Safe Browsing Cookies":
                print(each_file)
                yield each_file

def known_cookie_files():
    yield from [
        "C:\\Users\\sanga\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Network\\Cookies"
    ]

def load_auth_cookies():
    all_cookies = []
    for abs_file in known_cookie_files():
        loaded = browser_cookie3.chrome(cookie_file=abs_file)
        for cookie in loaded:
            all_cookies.append(cookie)
        

    relevant_cookies = {}
    for cookie in all_cookies:
        if "hoyolab" in cookie.domain:
            relevant_cookies[cookie.name] = cookie.value

    return relevant_cookies
