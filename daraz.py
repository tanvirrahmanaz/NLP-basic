from selenium import webdriver
import time

driver = webdriver.Chrome()

driver.get('https://www.daraz.com.bd/catalog/?spm=a2a0e.tm80335411.search.d_go&q=glass') #http request send hoi

driver.maximize_window()

text = driver.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div[1]/div/div[1]/div[2]/div[1]/div/div/div[2]/div[2]/a').text

print(text)


time.sleep(60)
driver.quit()