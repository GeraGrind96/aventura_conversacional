#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2021 by YOUR NAME HERE
#
#    This file is part of RoboComp
#
#    RoboComp is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RoboComp is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.
#

from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QApplication
from rich.console import Console
from genericworker import *

sys.path.append('/opt/robocomp/lib')
console = Console(highlight=False)

# If RoboComp was compiled with Python bindings you can use InnerModel in Python
# import librobocomp_qmat
# import librobocomp_osgviewer
# import librobocomp_innermodel

from usb_4_mic_array.tuning import Tuning
import usb.core
import usb.util
import time
import speech_recognition as sr
import random
import json

# Speech imports

max_queue = 100
charsToAvoid = ["'", '"', '{', '}', '[', '<', '>', '(', ')', '&', '$', '|', '#']
from google_speech import Speech
try:
	from Queue import Queue
except ImportError:
	from queue import Queue

# Microphone start

temas = ["música", "viajar", "cocina"]
keyword = ["girafa", "jirafa"]
afirmaciones = ["okey", "vale", "perfe", "si", "guay"]
negaciones = ["no", "que va", "para nada", "en absoluto"]

dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
Mic_tuning = Tuning(dev)
r = sr.Recognizer()
for i, microphone_name in enumerate(sr.Microphone.list_microphone_names()):
    print(microphone_name)
    if "ReSpeaker 4 Mic Array (UAC1.0)" in microphone_name:
        print("Micrófono seleccionado")
        m = sr.Microphone(device_index=i)

class Line:
    def __init__(self):
        self.next_possible_lines = []
        self.past_line = ""
        self.line_name = ""
        self.phrase = ""
        self.emotion = ""
        self.was_talked = False
        self.is_binary = 0

    def show_past_action(self):
        print("- "+self.past_line)

    def show_next_possible_actions(self):
        for line in self.next_possible_lines:
            print("- "+line)

class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        self.Period = 20
        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)
        self.user_name = ""
        self.line_list = []
        self.text_queue = Queue(max_queue)
        with open("lines.json", "r+") as possible_lines_json:
            possible_lines = json.load(possible_lines_json)
            for line in possible_lines:
                # print(line["line_name"])
                new_line = self.generate_line(line["line_name"], line["phrase"], line["next_possible_lines"], line["past_line"], line["emotion"], line["binary"])
                self.line_list.append(new_line)
        self.init_line = self.line_list[0]
        self.actual_line = ""
        self.final_line = self.line_list.pop()
        self.elapsed_time = time.time()
        self.counter = 0

    def __del__(self):
        """Destructor"""

    def setParams(self, params):
        return True

    @QtCore.Slot()
    def compute(self):
        # print("Vuelta")
        exist_voice = Mic_tuning.is_speech()
        # print (exist_voice)
        if(exist_voice == 1):
            key = self.recorder()
            if key in keyword:
                self.start()

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)

# Recording functions

    def recorder(self):
        with m as source:
            r.adjust_for_ambient_noise(source) 
            # print("Grabando")
            self.emotionalmotor_proxy.listening(True)     
            audio = r.listen(source, phrase_time_limit=3)
            self.emotionalmotor_proxy.listening(False)     
            try:
                record = r.recognize_google(audio, language="es-ES")
                return record
            except:
                return 0

    # For short answers (si, no)

    def recorder_binary(self):
        with m as source:
            r.adjust_for_ambient_noise(source) 
            # print("Grabando")
            self.emotionalmotor_proxy.listening(True)     
            audio = r.listen(source, phrase_time_limit=1.5)
            self.emotionalmotor_proxy.listening(False)     
            try:
                record = r.recognize_google(audio, language="es-ES")
                return record
            except:
                return 0

    def talker(self, text):
        lang = "es"
        speech = Speech(text, lang)
        self.emotionalmotor_proxy.talking(True)                        
        speech.play()
        self.emotionalmotor_proxy.talking(False)
        return

    def generate_line(self, name, phrase, next_lines, prev_line, emotion, is_binary): 
        line = Line()
        line.next_possible_lines = next_lines
        line.past_line = prev_line
        line.line_name = name
        line.phrase = phrase
        line.emotion = emotion
        line.is_binary = is_binary
        return line

    def choose_action(self, searched_action):
        global actions_list, actual_action
        for action in actions_list:
            if searched_action == action.action_name:
                actual_action = action

    def execute_action(self, action):
        action.to_say()

    def automatic_exit(self):
        self.talker("Déjame en paz.")

    def inicio_lineas(self):
        self.talker(self.actual_line.phrase)
        random_line = random.choice(self.actual_line.next_possible_lines)
        for line in self.line_list:
            if line.line_name == random_line:
                self.actual_line = line
                break
        self.talker(self.actual_line.phrase)
        if self.actual_line.is_binary == 0:
            response = self.recorder()

    def start(self):
        conversar = ""
        is_user_name = False
        conf = False
        self.talker("Que pasa")
        while True:
            self.talker("Quien coño eres. Pesao")
            self.counter = 0
            print(self.counter)
            self.user_name = self.recorder()
            while self.user_name == "" or self.user_name == 0:
                if self.user_name == 0:
                    print(self.counter)
                    if self.counter == 3:
                        self.automatic_exit()
                        return
                    else:
                        self.talker("Repite porfa")
                        self.counter += 1
                        print(self.counter)
                        self.user_name = self.recorder()
            self.counter = 0
            while is_user_name == False:
                self.talker("¿"+str(self.user_name)+"?")
                
                # print("¿Te llamas "+self.user_name+"?")
                is_name = self.recorder_binary()
                
                # print(is_name)
                if is_name in afirmaciones: 
                    is_user_name = True
                elif is_name in negaciones: 
                    self.talker("Por favor, repíteme tu nombre.")
                    # print("Por favor, repíteme tu nombre.")    
                    self.user_name = self.recorder()  
                else:
                    print(self.counter)
                    if self.counter == 3:
                        self.automatic_exit()
                        return
                    else:
                        self.talker("Repite porfa")   
                        self.counter += 1                 
                        is_name = self.recorder_binary()

               
            self.talker("Hola, "+self.user_name+". Me alegra hablar contigo.")
            # print("Hola, "+self.user_name+". Me alegra hablar contigo.")
            self.talker("¿Te apetece conversar un rato?")
            # print("¿Te apetece conversar un rato?")
            conversar = self.recorder_binary()
            self.counter = 0
            while True:               
                if(conversar in afirmaciones):
                    self.talker("¡Genial! Me apetece mucho hablar")
                    # print("¡Genial! Me apetece mucho hablar")
                    time.sleep(0.5)
                    self.inicio_conversacion()
                    return
                elif(conversar in negaciones):
                    self.talker("Pues no me molestes.")
                    # print("Bueno, quizá en otro momento.")
                    return 
                else:
                    if self.counter == 3:
                        self.automatic_exit()
                        return
                    self.talker("Repite porfa.")
                    # print("Perdona, no he entendido bien lo que has querido decir. Repítemelo, por favor.")
                    conversar = self.recorder_binary()
                    self.counter += 1 

    def inicio_conversacion(self):   
        hay_tema = False
        while hay_tema == False:
            self.talker(self.init_line.phrase)
            tema = self.recorder()
            self.counter = 0
            if any(word in tema for word in self.init_line.next_possible_lines): 
                self.talker("Perfecto, hablemos de "+ tema)
                hay_tema = True
                self.inicio_lineas()
            elif tema == 0:
                self.talker("Repite porfa")
                self.counter += 1
            elif self.counter == 3 and tema == 0:
                self.automatic_exit()
                return                
            else:
                self.talker("No sé mucho sobre ese tema. ¿Quieres hablar sobre"+random.choice(temas)+ "?")
                hay_tema = self.recorder_binary()
                if hay_tema in afirmaciones:
                    hay_tema = True
                    for tema in self.line_list:
                        if tema.line_name == temas:
                            self.actual_line = tema
                            break
                    self.inicio_lineas()
                elif hay_tema in negaciones:
                    self.talker("Vaya.")
                else:
                    self.talker("Repite porfa")
