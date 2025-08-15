import random
import time
import tkinter as tk
from tkinter import ttk
from collections import namedtuple

from PIL import Image, ImageTk


Spawn = namedtuple('Spawn', ('name', 'stand', 'prayer'))
Attempt = namedtuple('Attempt', ('spawn', 'tile_clicked', 'prayer_clicked', 'response_time'))


def create_styles():
    style = ttk.Style()
    
    style.configure('Wrong.TLabel', background='red')


def parse_spawn_data(file):
    with open(file, 'r') as f:
        lines = f.read().splitlines()
    
    line = 0

    def parse_spawn():
        nonlocal line
        
        name = lines[line]
        line += 2
        
        stand = lines[line][2:]
        line += 2
        
        prayer = 'Magic' if lines[line][2:] == 'Serpent' else 'Ranged'
        while line < len(lines) and lines[line] != '':
            line += 1
        line += 1
        
        return Spawn(name, stand, prayer)
    
    spawns = []
    while line < len(lines):
        spawns.append(parse_spawn())

    return spawns


class Answer(tk.Toplevel):
    _images = {}
    
    @staticmethod
    def image(name):
        if name not in Answer._images:
            Answer._images[name] = ImageTk.PhotoImage(Image.open(f'{name}.png'))
        return Answer._images[name]
    
    def __init__(self, *args, **kwargs):
        spawn = kwargs.pop('spawn')
        response_time = kwargs.pop('response_time')
        tile_clicked = kwargs.pop('tile')
        prayer_clicked = kwargs.pop('prayer')
        super().__init__(*args, **kwargs)
        
        self.title(spawn.name)
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        
        if tile_clicked == spawn.stand and prayer_clicked == spawn.prayer:
            if response_time < 1.2:
                message = f'Good job! Response time: {response_time:.02f}'
            else:
                message = f'Good clicks, but too slow! Response time: {response_time:.02f}'
        else:
            message = f'You suck! Response time: {response_time:.02f}'
        
        ttk.Label(
            self,
            text=message
        ).grid(row=0, column=0, columnspan=2, sticky='w', pady=(5, 0))
        stand_label = ttk.Label(self, text=spawn.stand)
        if tile_clicked != spawn.stand:
            stand_label.configure(style='Wrong.TLabel')
        stand_label.grid(row=1, column=0, sticky='w', pady=(5, 0), padx=5)
        stand_label_im = ttk.Label(
            self,
            image=Answer.image('middle') if spawn.stand == 'Middle' else Answer.image('north')
        )
        stand_label_im.grid(row=1, column=1, padx=5)
        prayer_label = ttk.Label(self, text=spawn.prayer)
        if prayer_clicked != spawn.prayer:
            prayer_label.configure(style='Wrong.TLabel')
        prayer_label.grid(row=2, column=0, sticky='w', pady=5, padx=5)
        prayer_im_label = ttk.Label(
            self,
            image=Answer.image('ranged') if spawn.prayer == 'Ranged' else Answer.image('magic')
        )
        prayer_im_label.grid(row=2, column=1, sticky='w', padx=5)
    
    def on_close(self):
        root.next_image()
        self.destroy()


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        self.spawns = kwargs.pop('spawns')
        
        super().__init__(*args, **kwargs)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        
        create_styles()
        
        self.pil_images = []
        self.images = []
        for spawn in self.spawns:
            self.pil_images.append(Image.open(f'{spawn.name}.png'))
            self.images.append(ImageTk.PhotoImage(self.pil_images[-1]))
        
        self.label = ttk.Label(self)
        self.label.grid(row=0, column=0, sticky='nsew')
        
        statistics_frame = ttk.Frame(self)
        statistics_frame.grid(row=0, column=0, sticky='nw')
        
        self.attempt_label = ttk.Label(statistics_frame, text='Attempts: 0; Perfect: 0')
        self.attempt_label.grid(row=0, column=0, padx=3, pady=(1, 0), sticky='w')
        
        self.tile_accuracy_label = ttk.Label(statistics_frame, text='Tile acc: 0.0%')
        self.tile_accuracy_label.grid(row=1, column=0, padx=3, pady=(1, 0), sticky='w')
        
        self.prayer_accuracy_label = ttk.Label(statistics_frame, text='Pray acc: 0.0%')
        self.prayer_accuracy_label.grid(row=2, column=0, padx=3, pady=(1, 0), sticky='w')
        
        self.response_time_label = ttk.Label(statistics_frame, text='Response: 0.00 +/- 0.00s')
        self.response_time_label.grid(row=3, column=0, padx=3, pady=1, sticky='w')
        
        self.bind('<KeyPress>', self.on_key_pressed)
        self.bind('<Button-1>', self.on_click)
        self.prayer_clicked = None
        self.tile_clicked = None
        
        self.history = []
        self.current_spawn = None
        self.current_answer = None
        self.last_show_time = time.time()
        self.next_image()
    
    def next_image(self):
        if self.current_answer is not None:
            self.current_answer.destroy()
            self.current_answer = None
            
        index = random.randint(0, len(self.spawns) - 1)
        self.current_spawn = self.spawns[index]
        self.label.configure(image=self.images[index])
        self.geometry(f'{self.pil_images[index].width}x{self.pil_images[index].height}')
        self.last_show_time = time.time()
        self.prayer_clicked = None
        self.tile_clicked = None
    
    def show_answer(self):
        response_time = time.time() - self.last_show_time
        self.current_answer = Answer(
            self,
            spawn=self.current_spawn,
            response_time=response_time,
            tile=self.tile_clicked,
            prayer=self.prayer_clicked
        )
        self.history.append(
            Attempt(self.current_spawn, self.tile_clicked, self.prayer_clicked, response_time)
        )
        self.update_statistics()
        x, y = self.winfo_x(), self.winfo_y()
        w, h = self.winfo_width(), self.winfo_height()
        self.current_answer.geometry(f'400x150+{x + w // 2 - 200}+{y + h // 2 - 75}')
    
    def update_statistics(self):
        perfects = sum(
            1 for a in self.history
            if a.spawn.stand == a.tile_clicked and a.spawn.prayer == a.prayer_clicked and a.response_time < 1.2
        )
        self.attempt_label.configure(text=f'Attempts: {len(self.history)}; Perfects: {perfects}')
        
        tile_acc = sum(1 for a in self.history if a.spawn.stand == a.tile_clicked) / len(self.history)
        self.tile_accuracy_label.configure(text=f'Tile acc: {100 * tile_acc:.01f}%')
        
        prayer_acc = sum(1 for a in self.history if a.spawn.prayer == a.prayer_clicked) / len(self.history)
        self.prayer_accuracy_label.configure(text=f'Pray acc: {100 * prayer_acc:.01f}%')
        
        s = sum(a.response_time for a in self.history)
        ss = sum(a.response_time**2 for a in self.history)
        n = len(self.history)
        mean = s / n
        
        if n == 1:
            std = 0
        else:
            std = ((ss - s**2/n) / (n-1)) ** .5
        
        self.response_time_label.configure(text=f'Response: {mean:.02f} +/- {std:.02f}')
        
    def on_key_pressed(self, event):
        if self.current_answer is not None:
            self.current_answer.destroy()
            self.current_answer = None
        
        self.show_answer()
    
    def on_click(self, event):
        if self.current_answer is not None:
            return
            
        if 874 <= event.x <= 902 and 472 <= event.y <= 504:
            self.prayer_clicked = 'Magic'
        elif 906 <= event.x <= 942 and 472 <= event.y <= 504:
            self.prayer_clicked = 'Ranged'
        
        if 358 <= event.x <= 384 and 315 <= event.y <= 342:
            self.tile_clicked = 'North'
        elif 385 <= event.x <= 408 and 315 <= event.y <= 342:
            self.tile_clicked = 'Middle'
        
        if self.tile_clicked is not None and self.prayer_clicked is not None:
            self.show_answer()
        

if __name__ == '__main__':
    root = App(spawns=parse_spawn_data('serpent_javelin.txt'))
    root.mainloop()
