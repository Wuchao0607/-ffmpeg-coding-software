import sys
import os
import json
import subprocess
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker 
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFileDialog, QMessageBox, QComboBox, QTextEdit,QMainWindow
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
import PyQt5.QtCore as Qt
from PyQt5.QtCore import QUrl
from Ui_main import Ui_MainWindow


class mywindow(QMainWindow, Ui_MainWindow):
    def __init__(self) -> None:
        super().__init__()  
        self.setupUi(self)
        self.init()
        self.length = 0  # 视频总时长
        self.position = 0  # 视频当前时长
        self.count = 0      # 定时器计数
        self.videoEndTime.setText('00:00')  # 初始时长显示
        self.videoNowTime.setText('00:00')
        
        self.input_resolution = None  # 分辨率
        self.input_frequency = None  # 帧率
        self.input_coder = None  # 编码器
        self.optionsDict = {  
            '否': [self.code_type.itemText(a) for a in range(self.code_type.count())],
            '是': ['多视点'],
        }  # 下拉文本
        
    def init(self):
        self.videowidget = QVideoWidget(self)
        self.playLayout.addWidget(self.videowidget)
        ########### 按键 ##############
        # 文件浏览按键
        self.inputbutton.clicked.connect(self.inputfile_get)
        self.outputbutton.clicked.connect(self.outputfile_get)
        self.inputInfoButton.clicked.connect(self.inputInfofile_get)
        self.encodeInfoButton.clicked.connect(self.encodeInfofile_get)
        self.playscanButton.clicked.connect(self.browse_palyfile)
        # 视频播放
        self.playButton.clicked.connect(self.videoPlay)# 播放
        self.stopButton.clicked.connect(self.videoPause)# 暂停
        # 编码相关
        self.startbutton.clicked.connect(self.encoder)# 开始编码
        self.RDPlotButton.clicked.connect(self.RDPlot)# 性能比较
        ########### 按键 ##############
        #下拉功能切换
        self.Function_2.currentIndexChanged.connect(self.updateOptions)
        
        # 设置播放按钮事件
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.videowidget)
        self.media_player.durationChanged.connect(self.get_duration_func)
        self.media_player.positionChanged.connect(self.progress)  # 媒体播放时发出信号

        # 设置 QTabWidget 的当前标签页改变时的响应函数  
        self.tabWidget.currentChanged.connect(self.onTabChanged)
        # 进度条
        # 释放
        self.videoslider.sliderReleased.connect(self.video_silder_released)
        # 按压拖动
        self.videoslider.sliderPressed.connect(self.video_silder_pressed)
        
    def updateOptions(self, index):  
        # 获取当前选中的类别  
        category = self.Function_2.currentText()  
  
        # 根据类别更新第二个 QComboBox 的选项
        self.code_type_1.clear()  
        if category in self.optionsDict:
            self.code_type_1.addItems(self.optionsDict[category])
################  文件选择  ##################
# 输入文件     
    def inputfile_get(self):
        if self.Function.currentText() == '转码':  # 转码，仅支持选择一个文件，拓展为.MP4
            filename, _ = QFileDialog.getOpenFileName(self, "选择视频文件", "",
                                                      "Video Files (*.mp4 *.mkv)")
            if filename:
                self.input1.setText(filename)
                self.get_video_info(self.result, filename, True)
        else:
            if self.Function_2.currentText() == '是':  # 编码且为多视点，支持选择多个.yuv文件
                options = QFileDialog.Options()  
                files, _ = QFileDialog.getOpenFileNames(self, "QFileDialog.getOpenFileNames()",
                            "", "All Files (*);;Python Files (*.yuv)", options=options)
                filename = ' '.join(files)
                if filename:
                    self.input1.setText(filename)
                    
            else:  # 编码且非多视点，仅支持选择单个.yuv文件
                filename, _ = QFileDialog.getOpenFileName(self, "选择视频文件", "", 
                                                          "Video Files (*.yuv)")
                if filename:
                    self.input1.setText(filename)
# 输出文件        
    def outputfile_get(self):
        filename = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if filename:
            self.input2.setText(filename)
# 输入视频信息文件 
    def inputInfofile_get(self):
        filename, _ = QFileDialog.getOpenFileName(self, "选择视频信息文件", "", "Text Files (*.txt)")
        if filename:
            self.inputInfo.setText(filename)
# 编码信息文件         
    def encodeInfofile_get(self):
        filename, _ = QFileDialog.getOpenFileName(self, "选择编码信息文件", "", "Text Files (*.txt)")
        if filename:
            self.encodeInfo.setText(filename)
            with open(filename, 'r', encoding="UTF-8") as file:
                lines = file.readlines()
            # 提取所需信息  
            coder = None  
            bitrate = None  
            Qscale = None  
            resolution = None  
            frequency = None   
            for line in lines:
                if '编码器' in line:
                    coder = line.split('编码器')[1].strip()
                    if coder in [self.code_type.itemText(a) for a in range(self.code_type.count())]:
                        index = [self.code_type.itemText(a) for a in range(self.code_type.count())].index(coder)
                        self.code_type.setCurrentIndex(index)
                elif '比特率(Kb/s)' in line:
                    bitrate = line.split('比特率(Kb/s)')[1].strip()
                    self.code_rate.setText(bitrate)
                elif '量化系数' in line:
                    Qscale = line.split('量化系数')[1].strip()
                    if int(Qscale) in range(0, 52):
                        self.QscaleInput.setText(Qscale)
                elif '分辨率' in line:
                    resolution = line.split('分辨率')[1].strip()
                    self.resolutionInput.setText(resolution)
                elif '帧率' in line:
                    frequency = line.split('帧率')[1].strip()
                    self.frequencyInput.setText(frequency)
                    
# 播放文件选择
    def browse_palyfile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "选择视频文件", "", "Video Files (*.mp4 *.mkv)")
        if filename:
            self.playInput.setText(filename)
            self.get_video_info(self.videoInfo, filename, False)
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
            # self.length = self.media_player.duration()
            # print(self.length)
            # self.videoEndTime.setText(self.get_duration())
################  文件选择  ##################

#########  视频播放  ##############
# 视频基本信息打印
    def get_video_info(self, a, file_path, flag):
        command = [  
        'ffprobe', '-v', 'error',  
        '-show_entries', 'format=duration,bit_rate,start_time,end_time',  
        '-show_entries', 'stream=width,height,r_frame_rate,codec_name,codec_long_name',  # 添加 codec_name 和 codec_long_name  
        '-of', 'json',  
        file_path  
    ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)  
    
        if result.returncode != 0:  
            print(f"Error running ffprobe: {result.stderr}")  
            return None  
    
        try:  
            video_info = json.loads(result.stdout)  
        except json.JSONDecodeError as e:  
            print(f"Error decoding JSON: {e}")  
            return None  

        format_info = video_info.get('format', {})  
        streams_info = video_info.get('streams', []) 

        codec_name = streams_info[0].get('codec_name', 'N/A')  
        # codec_long_name = streams_info[0].get('codec_long_name', 'N/A')         
        frame_rate = streams_info[0]['r_frame_rate'].split('/')  
        frame_rate = float(frame_rate[0]) / float(frame_rate[1]) if len(frame_rate) == 2 else float(frame_rate[0])  
         
        info_text = (  
            f"Duration: {format_info['duration']}s "  
            f"Frame Rate: {frame_rate} fps "  
            f"Bit Rate: {format_info.get('bit_rate', 'N/A')}\n"  
            f"Resolution: {streams_info[0]['width']}x{streams_info[0]['height']} "  
            f"Codec Name: {codec_name}"
        )
        
        a.setText(info_text)
        if flag:
            self.input_frequency, self.input_resolution, self.input_coder = frame_rate, f"{streams_info[0]['width']}x{streams_info[0]['height']}", codec_name

        # print(f"Codec Long Name: {codec_long_name}")  # 添加编码方式详细信息（可选） 

# 时长获取
    def get_duration_func(self):
        try:
            d = self.media_player.duration() + 1
            end_number = int(d / 1000 / 10) + 1
            #print('end_number = ' + str(end_number))
            sum = 0
            for n  in range (1,end_number):
                sum = sum + n

            vv = int((100 / (d / 1000)) * (d / 1000))
            self.videoslider.setMaximum(d)
            #self.video_slider.setMaximum(vv + sum)
            #print(100 + sum)

            all_second = int(d / 1000 % 60)  # 视频播放时间
            all_minute = int(d / 1000 / 60)
           
           
            if all_minute < 10:
                
                if all_second < 10:
                    
                    self.videoEndTime.setText('0' + str(all_minute) + ':0' + str(all_second))
                else:
                    
                    self.videoEndTime.setText('0' + str(all_minute) + ':' + str(all_second))
            else:
                
                if all_second < 10:
                    
                    self.videoEndTime.setText(str(all_minute) + ':0' + str(all_second))
                else:
                    
                    self.videoEndTime.setText(str(all_minute) + ':' + str(all_second))
        except Exception as e:
            pass
# 视频播放       
    def videoPlay(self):
        file_name = self.playInput.text()
        if file_name:  
            self.media_player.play()
        else:
            QMessageBox.critical(self, '错误', '输入文件为空!') 
# 暂停播放
    def videoPause(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:  
            self.media_player.pause()  
        elif self.media_player.state() == QMediaPlayer.PausedState:  
            self.media_player.play()
#########  视频播放  ##############

############  进度条  ################### 
# 释放      
    def video_silder_released(self):
        try:
            if self.media_player.state() != 0:
                self.media_player.setPosition(self.videoslider.value())
                self.media_player.play()
            else:  # 如果视频是停止状态，则拖动进度条无效
                self.video_slider.setValue(0) 
        except Exception as e:
            pass
# 按压/拖动（未释放）
    def video_silder_pressed(self):
        if self.media_player.state() != 0:
            self.media_player.pause()
    def progress(self):  # 视频进度条自动释放与播放时间
        try:
            self.length = self.media_player.duration() + 1
            self.position = self.media_player.position()          
            videosilder_maximum = self.videoslider.maximum()
            video_silder_value = int(((videosilder_maximum / (self.length / 1000)) * (self.position / 1000)))
            self.videoslider.setValue(video_silder_value + self.count)
            now_second = int(self.position / 1000 % 60)
            now_minute = int(self.position / 1000 / 60)
            if now_minute < 10:
                if now_second < 10:                  
                    self.videoNowTime.setText('0' + str(now_minute) + ':0' + str(now_second))
                else:
                    self.videoNowTime.setText('0' + str(now_minute) + ':' + str(now_second))
            else:               
                if now_second < 10:
                    self.videoNowTime.setText('' + str(now_minute) + ':0' + str(now_second))
                else:
                    self.videoNowTime.setText('' + str(now_minute) + ':' + str(now_second))
            self.count += 1
        except Exception as e:
            pass
#切换页面时确保视频暂停

    def onTabChanged(self, index):
        if index == 0:  # 切换到视频标签页  
            self.media_player.pause()  
       
        else:  # 切换到其他标签页 
            # 处于播放状态，暂停播放
            if self.media_player.state() == QMediaPlayer.PlayingState: 
                self.media_player.pause()
            # 处于媒体播放完毕状态，手动将播放器置为停止
            elif self.media_player.state ==  QMediaPlayer.EndOfMedia: 
                self.media_player.stop()
            # elif self.media_player.state() == QMediaPlayer.StoppedState:# 处于停止状态，手动置为停止，确保准确
            #     self.media_player.stop()      
############  进度条  ###################

#编码      
    def encoder(self):
        command = ['ffmpeg']
        ##########################编码##########################
        if self.Function.currentText() == '编码':
            ###############多视点#####################
            if self.Function_2.currentText() == '是':
                # 输入文件路径
                if self.input1.text() == "":
                    QMessageBox.critical(self, '错误', '输入文件为空!')
                    return
                else:
                    input_files = (self.input1.text()).split(' ')
                    print(input_files)
                # 文件信息
                if self.inputInfo.text() == "":
                    QMessageBox.critical(self, '错误', '信息文件为空!')
                    return
                else:
                    with open(self.inputInfo.text(), 'r', encoding="UTF-8") as file:
                        lines = file.readlines()
                    # 提取所需信息  
                    width = None  
                    height = None  
                    angle_resolution = None  
                    frame_count = None  
                    frame_frequency = None 
                    yuv_format = None  
                    bit_depth = None 
                    for line in lines:
                        if '空间分辨率' in line:  
                            width, height = map(int, line.split('空间分辨率')[1].strip().split('×'))  
                        if '角度分辨率' in line:  
                            # 注意：这里的角度分辨率对于YUV编码可能不是直接相关的参数，但我们可以读取它  
                            angle_resolution = tuple(map(int, line.split('角度分辨率')[1].strip().split('×')))  
                        if '帧数' in line:  
                            frame_count = int(line.split('帧数')[1].strip()) 
                        if 'YUV采样格式' in line:  
                            yuv_format = line.split('YUV采样格式')[1].strip()  
                        if '像素深度' in line:  
                            bit_depth = int(line.split('像素深度')[1].strip().replace('bit', ''))
                        if '帧率' in line:  
                            frame_frequency = int(line.split('帧率')[1].strip())
                        else: 
                            frame_frequency = 30
                            
                    inputinfo = [
                        '-s', f'{width}x{height}',
                        '-pix_fmt', f"""{('yuv420p' if yuv_format == '4:2:0' else ('yuv422p' if yuv_format == '4:2:2' else 'yuv444p'))}""",
                        # '-r', f"""{'30' if not frame_count else frame_count / (width * height * 1.5 / (4 if yuv_format == '4:2:0' else (6 if yuv_format == '4:2:2' else 8)))}""", 
                        '-r', f'{frame_frequency}'
                        ]
                # 编码器获取
                codec = self.code_type.currentText()
                # 输出文件
                # 输出文件路径
                if self.input2.text() == "":
                    output_fileDiatory = os.getcwd()
                    print(output_fileDiatory)
                else:
                    output_fileDiatory = self.input2.text()

                # 输出文件名
                if self.filenameinput.text() == "":
                    # 获取当前工作目录
                    current_directory = os.getcwd()
                    # 要检查的文件名
                    filename = "output.mp4"
                    # 构造文件的完整路径
                    filepath = os.path.join(current_directory, filename)
                    if os.path.isfile(filepath):
                        name = filename.split('.')[0]+'1'
                    else:
                        name = 'output'
                else:
                    name = self.filenameinput.text()
                    output_files = []
                    for index, file in enumerate(input_files):
                        output_files.append(output_fileDiatory+"\\"+name+str(index)+".mp4")   # 可自定义
                Cmd = [[] for _ in range(len(input_files))]  # 命令存储列表
                for index, inputfile in enumerate(input_files):
                    Cmd[index].append('ffmpeg')
                    Cmd[index].extend(inputinfo)
                    Cmd[index].extend(['-i', inputfile])
                    Cmd[index].extend(['-c:v', codec])
                # 码率获取Bit rate
                if self.code_rate.text() != "":
                    bitrate = self.code_rate.text() + "K"
                    for index in range(0, len(input_files)):
                        Cmd[index].extend(['-b:v', bitrate])
                    
                # 帧率获取frequency
                if self.frequencyInput.text() != "":
                    frequency = self.frequencyInput.text()
                    for index in range(0,len(input_files)): 
                        Cmd[index].extend(['-r', frequency])
                else:
                    frequency = ''

                # 量化系数获取
                if self.QscaleInput.text() != "":
                    if int(self.QscaleInput.text()) > 1 and int(self.QscaleInput.text()) < 31:
                        if self.code_rate.text() == "":
                            Qscale = self.QscaleInput.text()
                            for index in range(0,len(input_files)):
                                Cmd[index].extend(['-q:v', Qscale])
                        else:
                            QMessageBox.critical(self, '错误', '码率与量化系数冲突')
                            return
                    else:
                        QMessageBox.critical(self, '错误', '量化系数数值有误')
                        return
                # 分辨率获取
                if self.resolutionInput.text() != "":
                    resolution = self.resolutionInput.text()
                    for index in range(0,len(input_files)): 
                        Cmd[index].extend(['-vf', f'scale={resolution}'])
                else:
                    resolution = ''
                        
                for index in range(0,len(input_files)):
                    Cmd[index].append(output_files[index]) # 写入命令
                    
                    try:
                        subprocess.run(Cmd[index], check=True)
                        self.result.append(f'编码成功!\n输出文件: {output_files[index]}')
                    except subprocess.CalledProcessError:
                        QMessageBox.critical(self, '错误', '编码失败!')
                        return
            ###############单个文件###################
            else:
                # 输入文件路径
                if self.input1.text() == "":
                    QMessageBox.critical(self, '错误', '输入文件为空!')
                    return
                else:
                    input_file = self.input1.text()
                
                # 文件信息
                if self.inputInfo.text() == "":
                    QMessageBox.critical(self, '错误', '信息文件为空!')
                    return
                else:
                    with open(self.inputInfo.text(), 'r', encoding="UTF-8") as file:
                        lines = file.readlines()
                    # 提取所需信息  
                    width = None  
                    height = None  
                    angle_resolution = None  
                    frame_count = None  
                    frame_frequency = None
                    yuv_format = None  
                    bit_depth = None 
                    for line in lines:
                        if '空间分辨率' in line:  
                            width, height = map(int, line.split('空间分辨率')[1].strip().split('×'))  
                        if '角度分辨率' in line:  
                            # 注意：这里的角度分辨率对于YUV编码可能不是直接相关的参数，但我们可以读取它  
                            angle_resolution = tuple(map(int, line.split('角度分辨率')[1].strip().split('×')))  
                        if '帧数' in line:  
                            frame_count = int(line.split('帧数')[1].strip()) 
                        if 'YUV采样格式' in line:  
                            yuv_format = line.split('YUV采样格式')[1].strip()  
                        if '像素深度' in line:  
                            bit_depth = int(line.split('像素深度')[1].strip().replace('bit', ''))
                        if '帧率' in line:  
                            frame_frequency = int(line.split('帧率')[1].strip())
                        else:
                            frame_frequency = 30
                            
                    inputinfo = [
                        '-s', f'{width}x{height}',
                        '-pix_fmt', f"""{('yuv420p' if yuv_format == '4:2:0' else ('yuv422p' if yuv_format == '4:2:2' else 'yuv444p'))}""",
                        # '-r', f"""{'30' if not frame_count else frame_count / (width * height * 1.5 / (4 if yuv_format == '4:2:0' else (6 if yuv_format == '4:2:2' else 8)))}""", 
                        '-r', f'{frame_frequency}',
                        '-i', f'{input_file}'
                        ]
                    command.extend(inputinfo)
                # 编码器获取
                codec = self.code_type.currentText()
                command.extend(['-c:v', codec])
                # 码率获取Bit rate
                if self.code_rate.text() != "":
                    bitrate = self.code_rate.text() + "K"
                    command.extend(['-b:v', bitrate])

                # 帧率获取frequency
                if self.frequencyInput.text() != "":
                    frequency = self.frequencyInput.text()
                    command.extend(['-r', frequency])
                else:
                    frequency = ''

                # 量化系数获取
                if self.QscaleInput.text() != "":
                    if int(self.QscaleInput.text()) > 1 and int(self.QscaleInput.text()) < 31:
                        if self.code_rate.text() == "":
                            Qscale = self.QscaleInput.text()
                            command.extend(['-q:v', Qscale])
                        else:
                            QMessageBox.critical(self, '错误', '码率与量化系数冲突')
                            return
                    else:
                        QMessageBox.critical(self, '错误', '量化系数数值有误')
                        return
                # 分辨率获取
                if self.resolutionInput.text() != "":
                    resolution = self.resolutionInput.text()
                    command.extend(['-vf', f'scale={resolution}'])
                else:
                    resolution = ''
                
                # 输出文件
                # 输出文件路径
                if self.input2.text() == "":
                    output_fileDiatory = os.getcwd()
                    print(output_fileDiatory)
                else:
                    output_fileDiatory = self.input2.text()

                # 输出文件名
                if self.filenameinput.text() == "":
                    # 获取当前工作目录  
                    current_directory = os.getcwd()
                    # 要检查的文件名 
                    filename = "output.mp4"  
                    # 构造文件的完整路径  
                    filepath = os.path.join(current_directory, filename)
                    if os.path.isfile(filepath): 
                        name = filename.split('.')[0]+'1'
                    else:
                        name = 'output'
                else:
                    name = self.filenameinput.text()
                output_file = output_fileDiatory+"\\"+name+".mp4"  # 可自定义
                command.append(output_file) # 写入命令
                
                try:
                    subprocess.run(command, check=True)
                    self.result.setText(f'编码成功!\n输出文件: {output_file}')
                except subprocess.CalledProcessError:
                    QMessageBox.critical(self, '错误', '编码失败!')
                    return
                self.get_video_info(self.result, output_file, True)
                if (resolution, frequency) != ('', '') and (self.resolution, self.frequency) != (f'{width}x{height}', frame_frequency):
                    self.result.append('\n由于编码前后视频格式不一致，无法进行质量评估!')
                    return
                decode_file = output_fileDiatory+'\\'+'encoder.yuv'
                decode_cmd = [
                'ffmpeg',
                '-i', output_file,
                '-s', f'{width}x{height}',
                '-r', f'{frame_frequency}',
                '-pix_fmt', f"""{('yuv420p' if yuv_format == '4:2:0' else ('yuv422p' if yuv_format == '4:2:2' else 'yuv444p'))}""",
                decode_file
                ]
                try:
                    subprocess.run(decode_cmd, check=True)
                    
                except:
                    QMessageBox.critical(self, '错误', '计算过程解码失败!')
                    return
                try:
                    # 计算PSNR
                    psnr_cmd = [
                        'ffmpeg',
                        '-s', f'{width}x{height}',
                        '-r', f'{frame_frequency}',
                        '-pix_fmt', f"""{('yuv420p' if yuv_format == '4:2:0' else ('yuv422p' if yuv_format == '4:2:2' else 'yuv444p'))}""",
                        '-i', input_file,
                        '-s', f'{width}x{height}',
                        '-r', f'{frame_frequency}',
                        '-pix_fmt', f"""{('yuv420p' if yuv_format == '4:2:0' else ('yuv422p' if yuv_format == '4:2:2' else 'yuv444p'))}""",
                        '-i', decode_file,
                        '-lavfi', 'psnr', '-f', 'null', '-'
                    ]
                    
                    # 计算SSIM
                    ssim_cmd = [
                        'ffmpeg',
                        '-s', f'{width}x{height}',
                        '-r', f'{frame_frequency}',
                        '-pix_fmt', f"""{('yuv420p' if yuv_format == '4:2:0' else ('yuv422p' if yuv_format == '4:2:2' else 'yuv444p'))}""",
                        '-i', input_file,
                        '-s', f'{width}x{height}',
                        '-r', f'{frame_frequency}',
                        '-pix_fmt', f"""{('yuv420p' if yuv_format == '4:2:0' else ('yuv422p' if yuv_format == '4:2:2' else 'yuv444p'))}""",
                        '-i', decode_file,
                        '-lavfi', 'ssim', '-f', 'null', '-'
                    ]

                    # 运行命令并捕获输出来获取PSNR和SSIM
                    psnr_output = subprocess.run(psnr_cmd, stderr=subprocess.PIPE, encoding="utf-8", universal_newlines=True)
                    ssim_output = subprocess.run(ssim_cmd, stderr=subprocess.PIPE, encoding="utf-8", universal_newlines=True)
            
                    psnr_value = self.extract_psnr(psnr_output.stderr)
                    ssim_value = self.extract_ssim(ssim_output.stderr)
                    print(psnr_value)
                    print(ssim_value)

                    self.result.append(f'\nPSNR: {psnr_value} dB\nSSIM: {ssim_value}')
                    
                    if os.path.exists(decode_file):
                        os.remove(decode_file)
                except:
                    QMessageBox.critical(self, '错误', '视频质量计算失败!')
#########################转码#####################################
        else:
            # 输入文件路径
            if self.input1.text() == "":
                QMessageBox.critical(self, '错误', '输入文件为空!')
                return
            else:
                input_file = self.input1.text()
                command.extend(['-i', input_file])

            # 编码器获取
            codec = self.code_type.currentText()
            command.extend(['-c:v', codec])

            # 码率获取Bit rate
            if self.code_rate.text() != "":
                bitrate = self.code_rate.text() + "K"
                command.extend(['-b:v', bitrate])

            # 帧率获取frequency
            if self.frequencyInput.text() != "":
                frequency = self.frequencyInput.text()
                command.extend(['-r', frequency])
            else:
                frequency = ''

            # 量化系数获取
            if self.QscaleInput.text() != "":
                if int(self.QscaleInput.text()) > 1 and int(self.QscaleInput.text()) < 31:
                    if self.code_rate.text() == "":
                        Qscale = self.QscaleInput.text()
                        command.extend(['-q:v', Qscale])
                    else:
                        QMessageBox.critical(self, '错误', '码率与量化系数冲突')
                        return
                else:
                    QMessageBox.critical(self, '错误', '量化系数数值有误')
                    return
            # 分辨率获取
            if self.resolutionInput.text() != "":
                resolution = self.resolutionInput.text()
                command.extend(['-vf', f'scale={resolution}'])
            else:
                resolution = ''
            
            # 输出文件
            # 输出文件路径
            if self.input2.text() == "":
                output_fileDiatory = os.getcwd()
                print(output_fileDiatory)
            else:
                output_fileDiatory = self.input2.text()

            # 输出文件名
            if self.filenameinput.text() == "":
                # 获取当前工作目录  
                current_directory = os.getcwd()
                # 要检查的文件名 
                filename = "output.mp4"  
                # 构造文件的完整路径  
                filepath = os.path.join(current_directory, filename)
                if os.path.isfile(filepath): 
                    name = filename.split('.')[0]+'1'
                else:
                    name = 'output'
            else:
                name = self.filenameinput.text()
            output_file = output_fileDiatory+"\\"+name+".mp4"  # 可自定义
            command.append(output_file) # 写入命令
            
            # 执行命令行指令
            try:
                subprocess.run(command, check=True)
                self.result.setText(f'编码成功!\n输出文件: {output_file}')
            except subprocess.CalledProcessError:
                QMessageBox.critical(self, '错误', '编码失败!')
                return
            if (resolution != '' or frequency != '') and (self.resolution, self.frequency) != (resolution, frequency):
                self.result.append('\n由于编码前后视频格式不一致，无法进行质量评估!')
                return
            # if resolution is not None:
            #     # 切换分辨率
            #     change_cmd = [
            #         'ffmpeg', 
            #         '-i', input_file,
            #         '-vf', f'scale={resolution}',
            #         f"{input_file.split('.')[0]}_change.mp4"
            #     ]
            #     try:
            #         subprocess.run(change_cmd, check=True)
            #         input_file = f"{input_file.split('.')[0]}_change.mp4"
            #     except:
            #         QMessageBox.critical(self, '错误', '计算PSNR时分辨率修改出错!')
            #         return
                
            # 计算PSNR
            psnr_cmd = [
                'ffmpeg', '-i', input_file, '-i', output_file,
                '-lavfi', 'psnr', '-f', 'null', '-'
            ]            
            # 计算SSIM
            ssim_cmd = [
                'ffmpeg', '-i', input_file, '-i', output_file,
                '-lavfi', 'ssim', '-f', 'null', '-'
            ]
            # 运行命令并捕获输出来获取PSNR和SSIM
            psnr_output = subprocess.run(psnr_cmd, stderr=subprocess.PIPE, encoding="utf-8", universal_newlines=True)
            ssim_output = subprocess.run(ssim_cmd, stderr=subprocess.PIPE, encoding="utf-8", universal_newlines=True)

            psnr_value = self.extract_psnr(psnr_output.stderr)
            ssim_value = self.extract_ssim(ssim_output.stderr)
            # 显示
            self.result.append(f'\nPSNR: {psnr_value} dB\nSSIM: {ssim_value}')

    def extract_psnr(self, output):
        # 从输出中解析PSNR值
        for line in output.splitlines():
            if "average" in line:
                return line.split()[4]  # PSNR值在这个位置
        # return "无法计算PSNR"
        return print(output)

    def extract_ssim(self, output):
        # 从输出中解析SSIM值
        for line in output.splitlines():
            if "All" in line:  # 找到SSIM值所在行
                return line.split()[4]  # SSIM值在这个位置
        # return "无法计算SSIM"
        return print(output)   
# 绘图RD    
    def RDPlot(self):
        # 输出文件
        # 输出文件路径
        if self.input2.text() == "":
            output_fileDiatory = os.getcwd()
            print(output_fileDiatory)
        else:
            output_fileDiatory = self.input2.text()

        # 输出文件名
        if self.filenameinput.text() == "":
            name = 'temp'
        else:
            name = self.filenameinput.text()
        output_file = output_fileDiatory+"\\"+name+".mp4"  # 可自定义
        codecs = [f'{self.code_type_1.currentText()}', f'{self.code_type_2.currentText()}']
        if codecs[0] == codecs[1]:
            QMessageBox.critical(self, '错误', '编码器相同!')
            return
        # 定义比特率列表
        bitrates = ['100K', '200K', '500K', '1000K', '2000K', '3000K', '4000K']
        # 用于存储结果的字典  
        PSNR = {codec: [] for codec in codecs}
        SSIM = {codec: [] for codec in codecs}
        psnr_avrage = []
        ssim_avrage = []
########################################
##############非多视点###################
#######################################
        if self.Function_2.currentText() == '否':
            # 输入文件路径
            if self.input1.text() == "":
                QMessageBox.critical(self, '错误', '输入文件为空!')
                return
            else:
                input_file = self.input1.text()
##############################编码###################
                if self.Function.currentText() == '编码':  
                    # 文件信息
                    if self.inputInfo.text() == "":
                        QMessageBox.critical(self, '错误', '信息文件为空!')
                        return
                    else:
                        with open(self.inputInfo.text(), 'r', encoding="UTF-8") as file:
                            lines = file.readlines()
                        # 提取所需信息  
                        width = None  
                        height = None  
                        angle_resolution = None  
                        frame_count = None  
                        frame_frequency = None
                        yuv_format = None  
                        bit_depth = None 
                        for line in lines:
                            if '空间分辨率' in line:  
                                width, height = map(int, line.split('空间分辨率')[1].strip().split('×'))  
                            if '角度分辨率' in line:  
                                # 注意：这里的角度分辨率对于YUV编码可能不是直接相关的参数，但我们可以读取它  
                                angle_resolution = tuple(map(int, line.split('角度分辨率')[1].strip().split('×')))  
                            if '帧数' in line:  
                                frame_count = int(line.split('帧数')[1].strip()) 
                            if 'YUV采样格式' in line:  
                                yuv_format = line.split('YUV采样格式')[1].strip()  
                            if '像素深度' in line:  
                                bit_depth = int(line.split('像素深度')[1].strip().replace('bit', ''))
                            if '帧率' in line:  
                                frame_frequency = int(line.split('帧率')[1].strip())
                            else:
                                frame_frequency = 30
                                
                    
##############################转码###################                        
                else:
                    self.get_video_info(self.result, input_file, True) 
                    compare_file = input_file.split('.mp4')[0]+'.yuv'
                    command = [
                        'ffmpeg',
                        
                        '-i', input_file,
                        '-pix_fmt', 'yuv420p',
                        '-s', f'{self.input_resolution}',
                        '-r', f'{self.input_frequency}',
                        compare_file
                    ]
                    try:  
                        subprocess.run(command, check=True)  
                    except subprocess.CalledProcessError:  
                        QMessageBox.critical(self, '错误', '解码失败!') 
                        if os.path.exists(compare_file):  
                            os.remove(compare_file)
                        return
                            
            for codec in codecs:  
                psnr_sum = 0
                ssim_sum = 0
                
                for bitrate in bitrates:  
                    output_file = output_fileDiatory+"\\"+name+f'{codec}{bitrate}'+".mp4"
                    decode_file = output_fileDiatory+"\\"+name+f'{codec}{bitrate}'+".yuv"
                    # 编码视频
                    if self.Function.currentText() == '编码':
                        command = [  
                            'ffmpeg',
                            '-s', f'{width}x{height}',
                            '-pix_fmt', f"""{('yuv420p' if yuv_format == '4:2:0' else ('yuv422p' if yuv_format == '4:2:2' else 'yuv444p'))}""",
                            '-r', f'{frame_frequency}',
                            '-i', input_file,
                            '-c:v', codec, 
                            '-b:v', bitrate,
                            # '-s', f'{width}x{height}',
                            # '-pix_fmt', f"""{('yuv420p' if yuv_format == '4:2:0' else ('yuv422p' if yuv_format == '4:2:2' else 'yuv444p'))}""",
                            # '-r', f'{frame_count}',
                            output_file  
                        ]
                        decode_command = [
                        'ffmpeg',
                        '-i', output_file,  
                        '-s', f'{width}x{height}',
                        '-r', f'{frame_frequency}',
                        '-pix_fmt', f"""{('yuv420p' if yuv_format == '4:2:0' else ('yuv422p' if yuv_format == '4:2:2' else 'yuv444p'))}""",
                        decode_file
                        ]
                        psnr_cmd = [  
                        'ffmpeg',
                        '-s', f'{width}x{height}',
                        '-r', f'{frame_frequency}',
                        '-pix_fmt', f"""{('yuv420p' if yuv_format == '4:2:0' else ('yuv422p' if yuv_format == '4:2:2' else 'yuv444p'))}""",
                        '-i', input_file,
                        '-s', f'{width}x{height}',
                        '-r', f'{frame_frequency}',
                        '-pix_fmt', f"""{('yuv420p' if yuv_format == '4:2:0' else ('yuv422p' if yuv_format == '4:2:2' else 'yuv444p'))}""",
                        '-i', decode_file,  
                        '-lavfi', 'psnr', '-f', 'null', '-'  
                        ]  
                        ssim_cmd = [  
                        'ffmpeg', 
                        '-s', f'{width}x{height}',
                        '-r', f'{frame_frequency}',
                        '-pix_fmt', f"""{('yuv420p' if yuv_format == '4:2:0' else ('yuv422p' if yuv_format == '4:2:2' else 'yuv444p'))}""",
                        '-i', input_file,
                        '-s', f'{width}x{height}',
                        '-r', f'{frame_frequency}',
                        '-pix_fmt', f"""{('yuv420p' if yuv_format == '4:2:0' else ('yuv422p' if yuv_format == '4:2:2' else 'yuv444p'))}""",
                        '-i', decode_file, 
                        '-lavfi', 'ssim', '-f', 'null', '-'  
                        ]
          
                    else:
                        command = [  
                            'ffmpeg',
                            '-s', f'{self.input_resolution}',
                            '-r', f'{self.input_frequency}',
                            '-pix_fmt', 'yuv420p',
                            '-i', compare_file, 
                            '-c:v', codec,  
                            '-b:v', bitrate,  
                            output_file  
                        ]
                        decode_command = [
                        'ffmpeg', 
                        '-i', output_file,
                        '-s', f'{self.input_resolution}',
                        '-r', f'{self.input_frequency}',
                        '-pix_fmt', 'yuv420p',
                        decode_file
                        ]
                        psnr_cmd = [  
                        'ffmpeg',
                        '-s', f'{self.input_resolution}',
                        '-r', f'{self.input_frequency}',
                        '-pix_fmt', 'yuv420p',
                        '-i', compare_file,
                        '-s', f'{self.input_resolution}',
                        '-r', f'{self.input_frequency}',
                        '-pix_fmt', 'yuv420p',
                        '-i', decode_file,  
                        '-lavfi', 'psnr', '-f', 'null', '-'
                        ]  
                        ssim_cmd = [  
                        'ffmpeg', 
                        '-s', f'{self.input_resolution}',
                        '-r', f'{self.input_frequency}',
                        '-pix_fmt', 'yuv420p',
                        '-i', compare_file, 
                        '-s', f'{self.input_resolution}',
                        '-r', f'{self.input_frequency}',
                        '-pix_fmt', 'yuv420p',
                        '-i', decode_file,
                        '-lavfi', 'ssim', '-f', 'null', '-'
                        ]
                    try:  
                        subprocess.run(command, check=True)  
                    except subprocess.CalledProcessError:  
                        QMessageBox.critical(self, '错误', '编码失败!') 
                        if os.path.exists(output_file):
                            os.remove(output_file)
                        if os.path.exists(compare_file):
                            os.remove(compare_file)
                        return
                            # 跳过当前迭代 
                    try:  
                        subprocess.run(decode_command, check=True) 
                        
                    except subprocess.CalledProcessError:  
                        QMessageBox.critical(self, '错误', '解码失败!')
                        os.remove(output_file)
                        if os.path.exists(decode_file):
                            os.remove(decode_file)
                        if os.path.exists(compare_file):
                            os.remove(compare_file)
                        return
                        # 跳过当前迭代
                    os.remove(output_file)
                    # 计算 PSNR 和 SSIM
                    psnr_output = subprocess.run(psnr_cmd, stderr=subprocess.PIPE, encoding="utf-8", universal_newlines=True)  
                    ssim_output = subprocess.run(ssim_cmd, stderr=subprocess.PIPE, encoding="utf-8", universal_newlines=True)  
                    # 清理输出文件
                    if os.path.exists(decode_file):  
                        os.remove(decode_file)
                    # 获取计算结果
                    psnr_value = self.extract_psnr(psnr_output.stderr)  # 假设这个方法能够正确提取 PSNR 值  
                    ssim_value = self.extract_ssim(ssim_output.stderr)  # 假设这个方法能够正确提取 SSIM 值  
                    
                    #  转化为数值形式
                    print((psnr_value))
                    print((ssim_value))
                    PSNR[codec].append(float(psnr_value.split(':')[1]))
                    SSIM[codec].append(float(ssim_value.split(':')[1]))
                    psnr_sum += float(psnr_value.split(':')[1])
                    ssim_sum += float(psnr_value.split(':')[1])
                        
                psnr_avrage.append(psnr_sum/len(bitrates))
                ssim_avrage.append(ssim_sum/len(bitrates))
            # 将比特率字符串转换为整数（kbps）
            bitrates_int = [int(item.split('K')[0].strip()) for item in bitrates]
            self.Plot(bitrates_int, PSNR, SSIM, codecs, psnr_avrage)
            if self.Function.currentText() == '转码': 
                os.remove(compare_file)
        # 多视点性能比较
        else:
            QMessageBox.critical(self, '错误', '啊勒，这个功能还没写出来哩')

    def Plot(self, bitrates_int, PSNR, SSIM, codecs, psnr_avrage):
        # 创建图形和轴
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        # 设置颜色
        colors = ['tab:blue', 'tab:orange']
        # 设置PSNR的ylabel
        ax1.set_ylabel('PSNR (dB)')
        # 设置SSIM的ylabel  
        ax2.set_ylabel('SSIM')
        # 设置比特率的xlabel
        ax1.set_xlabel('Bitrate (kbps)')
        # 绘制PSNR曲线
        for i, codec in enumerate(PSNR.keys()):
            ax1.plot(bitrates_int, PSNR[codec], color=colors[i], marker='o', label=f'PSNR - {codec}', alpha=0.5)  
        # 绘制SSIM曲线
        for i, codec in enumerate(SSIM.keys()):
            ax2.plot(bitrates_int, SSIM[codec], color=colors[i], marker='^', label=f'SSIM - {codec}')  
        # 添加图例
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        # 由于我们为PSNR和SSIM设置了相同的x轴，我们可以只添加一个图例，但需要合并两个轴的图例项  
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        try:
            canvas = FigureCanvas(fig)
            canvas.draw()
            image = canvas.grab()
            label_size = self.RDLabel.size()
            image = image.scaled(label_size)
            self.RDLabel.setPixmap(image)
            #  计算BD_PSNR与BD_Rate
            BD_PSNR = str(psnr_avrage[0]-psnr_avrage[1])
            BD_Rate = (math.log(bitrates_int[1])/math.log(10)-
                       math.log(bitrates_int[2])/math.log(10)) - (math.log(PSNR[codecs[0]][1])/math.log(10) -
                    math.log(PSNR[codecs[1]][2])/math.log(10))
            self.result.append(f'PSNR: {(PSNR)} dB\nSSIM: {(SSIM)}\n')
            self.compareResult.append(f'Bitrates:{bitrates_int}\nBD-PSNR:{BD_PSNR} dB\nBD-Rate:{BD_Rate}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'绘图出错: {str(e)}')

     
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = mywindow()
    ex.show()
    sys.exit(app.exec_())