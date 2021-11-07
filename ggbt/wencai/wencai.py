# import wencai as wc
#
# # 若需中文字段则cn_col=True,chromedriver路径不在根目录下需指定execute_path
# wc.set_variable(cn_col=True, execute_path=r'C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chromedriver')
#
#
# strategy = wc.get_scrape_report(query='上证指数上穿10日均线',
#                                  start_date='2019-10-01',
#                                  end_date='2019-10-19',
#                                  period='1,2,3,4',
#                                  benchmark='hs000300')
#
# print(strategy.backtest_data)


from selenium import webdriver
import time

def main():
    chrome_driver = 'C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe'  #chromedriver的文件位置
    b = webdriver.Chrome(executable_path = chrome_driver)
    b.get('https://www.google.com')
    time.sleep(5)
    b.quit()

if __name__ == '__main__':
    main()