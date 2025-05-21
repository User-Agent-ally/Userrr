from lxml import etree  # 用于解析HTML页面
import requests  # 用来向目标网站发起网络请求 =》 代替浏览器来访问网站
import pyttsx3  # 文本转语音引擎（语音播报功能）
from pypinyin import lazy_pinyin  # 将中文城市名转为拼音
from threading import Thread,Event  # 多线程与事件通信
import random   # 生成随机User-Agent（反爬策略）
from vosk import Model, KaldiRecognizer # 离线语音识别库
import pyaudio  # 访问麦克风，处理音频流
import json # 解析JSON格式的识别结果

# 语音识别函数
def recognize_city():
    # 加载Vosk中文模型
    model = Model(r"E:\python\Lib\site-packages\vosk-model-small-cn-0.22")  # 模型文件夹路径

    # 初始化识别器，设置采样率为16kHz（与模型要求一致）
    recognizer = KaldiRecognizer(model, 16000)

    # 打开麦克风，配置音频流参数（单声道、16位深度、16kHz采样率）
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,channels=1,rate=16000,input=True,frames_per_buffer=8192)

    print("请说出城市名称（说完后请保持安静1秒）:")
    speak('请说出城市名称')
    # 实时语音识别功能
    while True:
        # 从麦克风读取音频数据
        data = stream.read(8192)
        if recognizer.AcceptWaveform(data):
            # 解析识别结果（JSON格式）
            result = json.loads(recognizer.Result())
            city_name = result.get("text", "").strip()
            if city_name:
                print(f"识别结果: {city_name}")
                break
            else:
                print("没有识别到内容，请手动输入！")
                speak("没有识别到内容，请手动输入！")
                break
    # 关闭音频流和资源（避免资源泄漏）
    stream.stop_stream()
    stream.close()
    p.terminate()
    return city_name

#天气查询函数
def funa(city_name):
    # 设置请求池，反爬策略
    UAlist = [
        'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36 Edg/136.0.0.0',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1 Edg/136.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0',
        'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 CrKey/1.54.248666 Edg/136.0.0.0'
    ]
    #从请求池中随机生成请求头
    ua = random.choice(UAlist)
    # 发送请求
    headers = {'User-Agent': ua}
    # 将中文城市名转为拼音
    pinyin_city = ''.join(lazy_pinyin(city_name))
    # 构造查询URL
    url = f'https://www.tianqi.com/{pinyin_city}/'
    # 发送HTTP请求获取网页内容
    res = requests.get(url, headers=headers)
    # 使用lxml解析HTML
    text = etree.HTML(res.text)
    # 通过XPath提取天气信息
    date1 = text.xpath('//dl[@class="weather_info"]//text()')
    # 清洗数据：合并文本、去除干扰项、按空格分割
    date1 = ''.join(date1)
    # 把xpath提取的信息中'[切换城市]'字符串替换为''
    date1 = date1.replace('[切换城市]', '').split()
    #解析数据，提取需要的信息
    s1=date1[0];s2=date1[1];s3=date1[2];s4=date1[4];s5=date1[7];s6=date1[8];
    if  s4!=s5:
        date2 = f'当前城市天气是：{s1}，日期是:{s2}{s3}，温度在{s4}到{s5}，{s6}'
        print(date2)
    else:
        date2 = f'当前城市天气是：{s1}，日期是:{s2}{s3}，温度是:{s4},{s6}'
        print(date2)
    return date2

# 语音播报函数
def speak(text,event=None):
    engine = pyttsx3.init()  # 初始化一个可以说话的对象
    engine.setProperty('rate', 730)  # 设置说话语速
    engine.setProperty('volume', 0.5)  # 设置音量
    engine.say(text)# 排队等待播报
    engine.runAndWait()# 阻塞直到播报完成
    if event:
        event.set()  # 通知主线程语音播报已完成

# 主函数
def main():
    # 调用录音函数
    city_name = recognize_city()
    # 调用天气查询函数
    if city_name:
        datess = funa(city_name)  # 调用funa函数并传入参数city_name
        datess = ' '.join(datess)
        # 使用多线程启动语音播报（非阻塞，允许用户同时输入）
        t2 = Thread(target=speak, args=(datess,))
        t2.start()
        t2.join()   # 等待播报完成（若无需等待可移除）

        print('语音播报完毕')
        speak('语音播报完毕')
    else:
        # 语音识别失败，进入手动输入模式
        prompt_event = Event()  # 创建事件对象用于线程通信
        while True:
            # 启动语音提示线程（非阻塞）
            t1 = Thread(target=speak, args=('请输入城市名称:', prompt_event))
            t1.start()

            print('提示:可以输入中文名称或者拼音(按f/F退出)')
            city_name = input('请输入城市名称:')

            prompt_event.wait() # 等待语音提示完成避免输入与播报冲突

            if city_name == 'f' or city_name == 'F':
                print('感谢使用')
                speak('感谢使用')
                break
            try:
                datess = funa(city_name)  # 调用funa函数并传入参数city_name
                datess = ' '.join(datess)

                t2 = Thread(target=speak, args=(datess,))
                t2.start()
                t2.join()

                print('语音播报完毕，是否继续查询城市天气(按f/F退出):', end='')
                speak('语音播报完毕，是否继续查询城市天气')
                pu = input()
                if pu == 'f' or pu == 'F':
                    print('感谢使用')
                    speak('感谢使用')
                    break
                else:
                    continue

            except Exception as e:
                if not city_name:
                    print("输入不能为空，请输入有效的城市名称或拼音")
                    speak('输入不能为空，请输入有效的城市名称或拼音')
                else:
                    print("输入城市名称或拼音有误，请重新输入")
                    speak("输入城市名称或拼音有误，请重新输入")

if __name__ == '__main__':
    main()

#问题一：input函数与语音播报不同步     解决：使用多线程Thread创建语音播报线程，允许主线程同时处理用户输入，实现异步交互。
#问题二：如果抢在播报之前输入城市名称会报错      解决：通过Event对象（prompt_event）实现线程同步，确保语音提示完成后再接收输入。
#问题三：爬取数据量大     解决：使用XPath精准定位天气信息节点，减少无效数据提取。
#问题四：输入城市名无法提取到天气信息     解决：使用文字转换模块
#问题五：无法调用谷歌语音识别     解决：使用vosk离线识别