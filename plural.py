import os
import time
import requests
import config
import re
from tinytag import TinyTag
from clint.textui import progress
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from slugify import slugify


def create_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print("\n<" + directory + "> folder created !")


def download(url, path):
    r = requests.get(url, stream=True)
    with open(path, 'wb') as f:
        total_length = int(r.headers.get('content-length'))
        for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length / 1024) + 1):
            if chunk:
                f.write(chunk)
                f.flush()


def length_of_video(clip_path):
    if not os.path.exists(clip_path):
        return 0
    return int(TinyTag.get(clip_path).duration)


def duration_to_seconds(duration):
    matches = re.match("(\d+)m (\d+)s", duration, re.I)
    if matches:
        return int(matches.group(1)) * 60 + int(matches.group(2))
    else:
        matches = re.match("(\d+)s", duration, re.I)
        if matches:
            return int(matches.group(1))
        else:
            matches = re.match("(\d+)m", duration, re.I)
            if matches:
                return int(matches.group(1))
    return 0


class Download:
    def __init__(self, link):
        self.link = link
        self.output = "Download"
        self.delay = config.Delay
        self.username = config.Username
        self.password = config.Password
        self.fail_downloads = 0
        self.try_download_times = config.TryDownloadTimes
        # for mute browser sounds
        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference("media.volume_scale", "0.0")
        self.browser = webdriver.Firefox(firefox_profile)
        print("Browser Initiated!")
        print("Loading .. " + self.link)
        self.login()
        self.download_episodes()
        self.browser.close()
        print("\nTotal fail downloads count:" + str(self.fail_downloads))

    def login(self):
        self.browser.get("https://app.pluralsight.com/id?redirectTo=" + self.link)
        time.sleep(self.delay)
        # fill in the login form
        self.browser.find_element_by_id("Username").send_keys(self.username)
        self.browser.find_element_by_id("Password").send_keys(self.password)
        # click the sign in button
        print("Logging in ...", end=" ")
        self.browser.find_element_by_id("login").click()
        time.sleep(self.delay)
        self.pause_playback()

    def pause_playback(self):
        body = self.browser.find_element_by_css_selector("body")
        body.send_keys(Keys.SPACE)

    def download_episodes(self):
        all_module_class = ".module"
        closed_module_class = ".module:not(.open)"
        opened_module_class = ".module.open"

        # fetching course title
        self.output = self.browser.find_element_by_id("course-title").text
        # create output folder with course name
        create_dir(self.output)
        # click all closed sections to open
        [closed_module.click() for closed_module in self.browser.find_elements_by_css_selector(closed_module_class)]

        # all modules
        all_modules = self.browser.find_elements_by_css_selector(all_module_class)
        # all modules need to be opened
        assert len(self.browser.find_elements_by_css_selector(opened_module_class)) == len(all_modules)

        for i in range(len(all_modules)):
            # fetching module title
            module_title = all_modules[i].find_element_by_tag_name("h2").text
            # create module folder
            module_folder = self.output + "/" + str(i) + "-" + slugify(module_title)
            create_dir(module_folder)
            # fetching clips each module
            all_clips = all_modules[i].find_elements_by_tag_name("li")
            for j in range(len(all_clips)):
                print("\n")
                clip = all_clips[j]
                clip_title = clip.find_element_by_tag_name("h3").text
                clip_duration = clip.find_element_by_css_selector(".side-menu-clip-duration").text
                clip_file = str(j) + "-" + slugify(clip_title) + ".mp4"
                clip_path = module_folder + "/" + clip_file
                validated = False
                try_download = 0
                while not validated and not try_download == self.try_download_times:
                    clip.click()
                    time.sleep(self.delay)
                    self.pause_playback()
                    if not os.path.exists(clip_path):
                        if try_download > 0:
                            print("Retrying..", end=" ")
                        print("Downloading: ", clip_file)
                        download(self.get_video_link(), clip_path)
                    else:
                        print("Already downloaded..")

                    print("Validation downloaded clip..", end=" ")
                    if length_of_video(clip_path) - 2 < duration_to_seconds(clip_duration) < length_of_video(
                            clip_path) + 2:
                        validated = True
                        print(" + Validated")
                    else:
                        print(" - Not Valid")
                        try_download = try_download + 1
                        if try_download != self.try_download_times:
                            os.remove(clip_path)
                        else:
                            self.fail_downloads = self.fail_downloads + 1

    def get_video_link(self):
        video_elt = self.browser.find_element_by_tag_name('video')
        link = video_elt.get_attribute("src")
        return link
