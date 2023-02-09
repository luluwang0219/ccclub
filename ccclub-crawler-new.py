from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import time
from PIL import Image
import io
import ddddocr

user_data = {
  "depart":"5",
  "dest":"7",
  "date":"二月 16, 2023",
  "expect_time":"10:00",
  "depart_time":"",
  "dest_time":"",
  "id":"Your ID",
  "duration":"",
  "ticket_num":"",
  "car":"",
  "seat":"",
  "payment_deadline":"",
  "line_page1_text":"",
  "line_page2_text":""
}

def browser():
    # 瀏覽器選擇
    my_options=Options()
    my_options.add_argument('--start-maximized')
    my_options.add_experimental_option("excludeSwitches", ['enable-automation']) # 不顯示“正受到自動測試軟體控制”
    my_options.add_argument('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0') # 改變uesr-agent
    my_options.add_argument("disable-blink-features=AutomationControlled") # 告訴chrome去掉了webdriver痕跡
    my_options.chrome_executable_path='C:/Users/User/Documents/pp_python/chromedriver.exe'
    driver=webdriver.Chrome(options=my_options)
    return driver

def page1(driver, depart, dest, expectime, date):
    # 進入高鐵網頁
    driver.get('https://irs.thsrc.com.tw/IMINT/')

    # 同意cookie
    driver.find_element_by_xpath('//*[@id="cookieAccpetBtn"]').click()

    # 代入使用者欲購買的車票資訊
    # 1.起程站 (格式：字典)
    start = Select(driver.find_element_by_name('selectStartStation'))
    start.select_by_value(depart) 

    # 2.抵達站 (格式：字典)
    end = Select(driver.find_element_by_name('selectDestinationStation'))
    end.select_by_value(dest)

    # 3.出發時間 (格式：10:00)
    start_time = Select(driver.find_element_by_name('toTimeTable'))
    start_time.select_by_visible_text(expectime)

    # 4.出發日期 (格式：十二月 27, 2022)
    driver.find_element_by_xpath('//*[@id="BookingS1Form"]/div[3]/div[2]/div/div[1]/div[1]/input[2]').click()
    start_date = driver.find_element_by_xpath(f'//*[@id="mainBody"]/div[9]/div[2]/div/div[2]/div[@class="dayContainer"]/span[@aria-label="{date}"]')
    start_date.click()


def verification(driver):
    # 5.處理驗證碼
    # time.sleep(1)
    img = driver.find_element_by_id('BookingS1Form_homeCaptcha_passCode').screenshot_as_png
    imageStream = io.BytesIO(img)
    im = Image.open(imageStream)
    im.save('captcha3.png')
    ocr = ddddocr.DdddOcr()
    with open('captcha3.png', 'rb') as f:
        img_bytes = f.read()
    CAPTCHA = ocr.classification(img_bytes)
    # print(CAPTCHA)
    blank = driver.find_element_by_xpath('//*[@id="securityCode"]')
    blank.clear()
    blank.send_keys(CAPTCHA)
    # time.sleep(4)
    driver.find_element_by_xpath('//*[@id="SubmitButton"]').click()
    time.sleep(1)

def page2_booking(driver):
    # 選擇"車程時間最短"的車次
    durations = driver.find_elements_by_xpath('//*[@class="duration"]/span[contains(text(), ":")]')
    duration_lst = []
    for duration in durations:
        duration_lst.append(duration.text)

    trains = driver.find_elements_by_xpath('//*[@id="QueryCode"]')
    train_lst = []
    for train in trains:
        train_lst.append(train.text)

    dic_train_duration={}
    for duration, train in zip(duration_lst, train_lst):
        dic_train_duration[train]=duration
    duration_train_lst = sorted(dic_train_duration.items(), key=lambda item:item[1])
    expected_train = duration_train_lst[0][0] # 車次
    expected_duration = duration_train_lst[0][1] # 車程時間
    # 選擇排序後最快的班次訂票
    driver.find_element_by_xpath(f'//*[@class="duration"]/span[contains(text(), "{expected_train}")]').click()
    
    # 確認車次
    driver.find_element_by_xpath('//*[@id="BookingS2Form"]/section[2]/div/div/input').click()
    return expected_train, expected_duration

def page3_user_info(driver, ID):
    # 代入使用者自身資料(身分證(必填)、電話與電子郵件)
    userid = driver.find_element_by_xpath('//*[@id="idNumber"]')
    userid.send_keys(ID) # 身分證字號

    # 輸入高鐵會員資訊(預設為有會員)
    driver.find_element_by_xpath('//*[@id="memberSystemRadio1"]').click()
    driver.find_element_by_xpath('//*[@id="memberShipCheckBox"]').click()

    # 完成訂位
    driver.find_element_by_xpath('//*[@id="BookingS3FormSP"]/section[2]/div[3]/div[1]/label/input').click()
    driver.find_element_by_xpath('//*[@id="isSubmit"]').click()
    driver.find_element_by_xpath('//*[@id="btn-custom2"]').click()
    time.sleep(1)

    # 若沒有會員
    try:
        if driver.find_element_by_class_name('feedbackPanelERROR'):
            driver.find_element_by_xpath('//*[@id="memberSystemRadio3"]').click()
            driver.find_element_by_xpath('//*[@id="isSubmit"]').click()  
    except:
        pass

def page4_return_ticket(driver,expected_train,expected_duration):
    try:
        # 回傳訂位資訊
        # driver.save_screenshot('screenshot-ticket.png') # 截圖
        ticket_num = driver.find_element_by_class_name('pnr-code').text # 訂位代號
        payment_deadline = driver.find_element_by_class_name('status-unpaid').text # 付款期限
        depart_time = driver.find_element_by_id('setTrainDeparture0').text # 出發時間
        arrival_time = driver.find_element_by_id('setTrainArrival0').text # 抵達時間
        seat = driver.find_element_by_class_name('seat-label').text # 座位
        # print(ticket_num, payment_deadline, depart_time, arrival_time, expected_duration, expected_train, seat, sep='\n')
        user_data['car'] = expected_train
        user_data['duration'] = expected_duration
        user_data['depart_time'] = depart_time
        user_data['dest_time'] = arrival_time
        user_data['seat'] = seat
        user_data['ticket_num'] = ticket_num
        user_data['payment_deadline'] = payment_deadline
    except:
        user_data['line_page2_text'] = '查無可售車次或選購的車票已售完'
    driver.close()

def verification_circle(driver):
    count = 0
    while True:
        if count<5:
            try:
                driver.find_element_by_xpath('//*[@id="mainBody"]/div[5]/div[1]/div/div[3]/p/span[1]').get_attribute('class')
                print('correct')
                break
            except:
                try:
                    sold_out_msg = driver.find_element_by_xpath('//*[@id="feedMSG"]/span/ul/li/span').text
                    print(sold_out_msg)
                    if sold_out_msg=='去程查無可售車次或選購的車票已售完，請重新輸入訂票條件。':
                        user_data['line_page2_text'] = '查無可售車次或選購的車票已售完'
                        print(user_data)
                        driver.close()
                except:
                    pass
                time.sleep(0.5)
                # print('error')
                ticketnum = Select(driver.find_element_by_name('ticketPanel:rows:0:ticketAmount'))
                ticketnum.select_by_visible_text('1')  
                print(f'錯誤{count}次') 
                count+=1
                verification(driver)
        else:
            user_data['line_page1_text'] = '請稍後...'
            # print(user_data)
            driver.close()
            count = 0
            driver=browser()
            page1(driver, user_data['depart'], user_data['dest'], user_data['expect_time'], user_data['date'])
            verification(driver)

def main():
    driver=browser()
    page1(driver, user_data['depart'], user_data['dest'], user_data['expect_time'], user_data['date'])
    verification_circle(driver)
    expected_train,expected_duration = page2_booking(driver)
    page3_user_info(driver, user_data['id'])
    page4_return_ticket(driver,expected_train,expected_duration)

if __name__ == '__main__':
    main()
    print(user_data)