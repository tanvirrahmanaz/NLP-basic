from selenium import webdriver
import time

driver = webdriver.Chrome()

driver.get('https://www.daraz.com.bd/catalog/?spm=a2a0e.tm80335411.search.d_go&q=glass') #http request send hoi

driver.maximize_window()