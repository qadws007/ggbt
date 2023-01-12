

def time_run(func):
    import time
    def inner(*args, **kwargs):
        t_start = time.time()
        func(*args, **kwargs)
        t_end = time.time()
        print("一共花费了 {:.4f} 秒时间".format(t_end - t_start, 4))

    return inner


@time_run
def screenshot_qt5():
    #截全屏，带保存，不带保存，均为0.07秒
    from PyQt5.QtWidgets import QApplication
    import win32gui
    import sys
    # 这个是截取全屏的
    hwnd = win32gui.FindWindow(None, 'C:/Windows/system32/cmd.exe')
    app = QApplication(sys.argv)
    screen = QApplication.primaryScreen()
    img = screen.grabWindow(hwnd).toImage()
    #img.save("screenshot.jpg")


@time_run
def screenshot_pyautogui():
    # 截全屏，带保存0.09，不带保存，为0.07秒
    import pyautogui
    import cv2
    import numpy as np

    img = pyautogui.screenshot(region=[0, 0, 1920, 1080])  # 分别代表：左上角坐标，宽高
    # 对获取的图片转换成二维矩阵形式，后再将RGB转成BGR
    # 因为imshow,默认通道顺序是BGR，而pyautogui默认是RGB所以要转换一下，不然会有点问题
    img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    cv2.imwrite("screenshot.jpg", img)
    #cv2.imshow("截屏", img)
    #cv2.waitKey(0)

@time_run
def screenshot_pil():
    # 截全屏，带保存0.07，不带保存，为0.06秒
    from PIL import ImageGrab
    # img = ImageGrab.grab(bbox=(250, 161, 1141, 610))
    image = ImageGrab.grab()
    #image.save("screen.jpg")
    # PIL image to OpenCV image
    #image.show()

if __name__=="__main__":
    scrren_cut()