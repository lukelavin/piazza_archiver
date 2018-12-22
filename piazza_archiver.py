from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import time
from pathlib import Path


def append_tabbed(s, added):
    lines = added.split('\n')
    for line in lines:
        s += '\t' + line + '\n'
    return s


# instantiate a chrome options object so you can set the size and headless preference
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
# chrome_options.add_argument("--window-size=1920x1080")

driver = webdriver.Chrome('drivers\\chromedriver.exe', chrome_options=chrome_options)

driver.set_page_load_timeout(10)

driver.get('https://piazza.com/class/<insert class code here>')
time.sleep(2)
driver.find_element_by_name('email').send_keys('<insert email here>')
driver.find_element_by_name('password').send_keys('<insert password here>')
driver.find_element_by_id('modal_login_button').click()
time.sleep(2)

MAX_POST_NUM = 3046

for i in range(1, MAX_POST_NUM):
    out = ''
    driver.get('https://piazza.com/class/<insert class code here>?cid=' + str(i))
    time.sleep(2)
    out += '==========================================================\n'
    out += "Post " + str(i) + '\n'

    try:
        WebDriverWait(driver, 1).until(ec.alert_is_present(), 'No piazza alert')

        alert = driver.switch_to.alert
        alert.accept()
        out += "Private Post - Alert handled\n\n"
    except TimeoutException:
        title = ""
        try:
            title = driver.find_element_by_xpath('//*[@id="view_quesiton_note"]/h1').text
        except NoSuchElementException:
            out += "Content not Available\n\n"
            continue

        out += "Public Post - Finding content\n---\n"
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

        try:
            folders = "Folders: "
            folder_list = []
            for folder in driver.find_elements_by_xpath('//*[@id="view_quesiton_note"]/div[2]/span/*'):
                folders += folder.text + ', '
                folder_list.append(folder.text)
            folders = folders[:len(folders) - 2]
            out += folders + '\n'
        except NoSuchElementException:
            out += 'Folder(s) not found\n\n'
        print(i, title)

        # sanitize title
        illegal_characters = ('/', '\\', '?', '%', '*', ':', '|', '"', '<', '>', '.')
        for ch in illegal_characters:
            title = title.replace(ch, '')

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
