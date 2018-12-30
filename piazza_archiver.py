from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import time
from pathlib import Path

# Constants

# Post numbers to try to archive
# If you want to archive all posts, use the cid from the latest post's url + 1 as POST_RANGE_END
# If you want things to go faster, maybe run multiple instances of this program, each iterating over different post nums
POST_RANGE_START = 1                   # (inclusive)
POST_RANGE_END = 3046                  # (exclusive)

# From the url of the class on Piazza -> https://piazza.com/class/[THIS IS THE CLASS CODE]
# For CS180 it was jku2ev85e2a4x1
CLASS_CODE = 'jku2ev85e2a4x1'

# Email used to login to Piazza
EMAIL = ''
# Password used to login to Piazza
PASSWORD = ''


def append_tabbed(s, added):
    lines = added.split('\n')
    for line in lines:
        s += '\t' + line + '\n'
    return s


# instantiate a chrome options object so you can set the size and headless preference
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')

# get the web driver with the proper options
print('Instantiating web driver')
driver = webdriver.Chrome('drivers\\chromedriver.exe', chrome_options=chrome_options)
driver.set_page_load_timeout(15)

print('Getting class page')
driver.get('https://piazza.com/class/' + CLASS_CODE)
time.sleep(2)
print('Logging in')
driver.find_element_by_name('email').send_keys(EMAIL)
driver.find_element_by_name('password').send_keys(PASSWORD)
driver.find_element_by_id('modal_login_button').click()
time.sleep(2)

for i in range(POST_RANGE_START, POST_RANGE_END):
    driver.get('https://piazza.com/class/' + CLASS_CODE + '?cid=' + str(i))
    out = '==========================================================\n'
    out += "Post " + str(i) + '\n'

    try:
        WebDriverWait(driver, 1).until(ec.alert_is_present(), 'No piazza alert')

        alert = driver.switch_to.alert
        alert.accept()
        print('Private Post - Alert handled')
        continue
    except TimeoutException:
        pass

    title = ''
    try:
        title = driver.find_element_by_xpath('//*[@id="view_quesiton_note"]/h1').text
    except NoSuchElementException:
        out += "Content not Available\n\n"
        continue

    out += 'Public Post - Finding content\n---\n'
    # title
    out += "Title: " + title + '\n'
    out += '---\n'

    # question/note text
    out += "Post text:\n" + driver.find_element_by_xpath('//*[@id="view_quesiton_note"]').text + '\n'
    out += '---\n'

    # student answer
    try:
        out += "Student answer:\n" + driver.find_element_by_xpath('//*[@id="s_answer"]/div[3]/div[1]').text + '\n'
    except NoSuchElementException:
        out += 'No Student Answer\n'
    out += '---\n'

    # instructor answer
    try:
        out += "Instructor answer:\n" + driver.find_element_by_xpath('//*[@id="i_answer"]/div[2]/div[1]').text + \
               '\n'
    except NoSuchElementException:
        out += 'No Instructor Answer\n'
    out += '---\n'

    # follow-up discussions
    out += 'Follow-ups:\n'
    try:
        # get each follow up "thread"
        followupNum = 1
        for followup in driver.find_elements_by_xpath('//*[@id="clarifying_discussion"]/div[2]/*'):
            followupHead = ''
            # get the text in the head of that thread
            try:
                followupHead = followup.find_element_by_class_name('main_followup').text
                out += "Follow-up " + str(followupNum) + ":" + '\n'
                out += followupHead + '\n'
            except NoSuchElementException:
                out += 'End of Follow-Ups\n---\n'
                break

            # get the text of each reply
            try:
                for reply in followup.find_elements_by_class_name('discussion_replies'):
                    out = append_tabbed(out, reply.text)
            except NoSuchElementException:
                pass

            out += '---\n'
            followupNum = followupNum + 1
    except NoSuchElementException:
        out += 'Error finding follow-ups\n\n'

    # get the folders that the post is labeled
    folder_list = []
    try:
        folders = 'Folders: '
        for folder in driver.find_elements_by_xpath('//*[@id="view_quesiton_note"]/div[2]/span/*'):
            folders += folder.text + ', '
            folder_list.append(folder.text)
        folders = folders[:len(folders) - 2]
        out += folders + '\n'
    except NoSuchElementException:
        out += 'Folder(s) not found\n\n'
    print(i, title)

    # remove illegal characters from the title in order to use the title as a file name
    illegal_characters = ('/', '\\', '?', '%', '*', ':', '|', '"', '<', '>', '.')
    for ch in illegal_characters:
        title = title.replace(ch, '')

    # write the post to a file appropriately named in the proper folder(s)
    for folder_name in folder_list:
        filename = Path('archive/' + folder_name)
        filename.mkdir(parents=True, exist_ok=True)
        filename = Path('archive/' + folder_name + '/' + title + '.txt')
        filename.touch(exist_ok=True)
        try:
            with open('archive/' + folder_name + '/' + title + '.txt', 'w+') as file:
                file.write(out)
        except UnicodeEncodeError:
            print('Unicode error')

driver.close()
driver.quit()
