import tkinter as tk
import math
import time

class Window:
    def __init__(self):
        self.crossids = set()
        self.upids = set()
        self.mode = "insert"

        self.linedotid = {}

        self.last_toggle = 0
        self.window = tk.Tk()

        self.window.geometry("600x300")
        self.canvas = tk.Canvas(self.window, width=700, height=300)
        self.canvas.bind("<Button-1>", self.clicked)
        self.window.bind("<d>", self.toggle)
        self.window.bind("<i>", self.toggle)
        self.window.bind("<q>", self.toggle)
        self.canvas.pack()

        self.canvas.create_rectangle(0, 270, 600, 350, fill="black")

        self.pairs = dict()
       
        self.canvas.bind('<Motion>', self.motion)
        self.last_highlight = -1





        self.window.mainloop()


    def query(self, t):
        existlist = []
        for line in self.crossids:
            c = self.canvas.coords(line)
            if c[2] > t and c[0] <= t:
                existlist.append(270- c[1])

        return sorted(existlist)


    def motion(self, event):
        if self.mode == "delete":
            t, y = event.x, event.y
            if y >= 270:
                closest = -1
                dist = float('inf')
                for line in self.upids:
                    c = self.canvas.coords(line)
                    if c[0] <= t+4 and c[0]>=t-4:
                        if abs(t-c[0]) < dist:
                            closest = line
                            dist = abs(t-c[0])
                if closest >= 0:
                    if self.last_highlight != -1 and self.last_highlight != closest:
                        self.canvas.itemconfig(self.last_highlight, fill='black')
                    elif self.last_highlight == -1:
                        self.canvas.itemconfig(closest, fill='red')
                    
                    self.last_highlight = closest
                else:
                    if self.last_highlight != -1:
                        self.canvas.itemconfig(self.last_highlight, fill='black')
                    self.last_highlight = -1
            
            else:
                closest = -1
                dist = float('inf')
                for line in self.crossids:
                    c = self.canvas.coords(line)
                    if c[1] <= y+4 and c[1]>=y-4 and c[0] <= t and c[2] >= t:
                        if abs(y-c[1]) < dist:
                            closest = line
                            dist = abs(y-c[1])
                if closest >= 0:
                    if self.last_highlight != -1 and self.last_highlight != closest:
                        self.canvas.itemconfig(self.last_highlight, fill='black')
                    elif self.last_highlight == -1:
                        self.canvas.itemconfig(closest, fill='red')
                    
                    self.last_highlight = closest
                else:
                    if self.last_highlight != -1:
                        self.canvas.itemconfig(self.last_highlight, fill='black')
                    self.last_highlight = -1


    def clicked(self, event):
        if self.mode == "query":
            print(self.query(event.x))
        elif self.mode == "insert":
            self.insert(event.x, event.y)
        elif self.mode == "delete":
            self.delete(event.x, event.y)

    def toggle(self, event):
        if time.time() - self.last_toggle > .1:
            print(event.keysym)
            self.last_toggle = time.time()
            if event.keysym == "d":
                self.mode = "delete"
            elif event.keysym == "i":
                self.mode = "insert"
            elif event.keysym == "q":
                self.mode = "query"
            if self.last_highlight != -1:
                self.canvas.itemconfig(self.last_highlight, fill='black')
            self.last_highlight = -1

    def insert(self, t, y):
        # delete min
        if y >= 270:
            miny = -1
            minid = -1
            for line in self.crossids:
                c = self.canvas.coords(line)
                if c[0] <= t and c[2]>=t:
                    if c[1] > miny:
                        miny = c[1]
                        minid = line

            id = self.canvas.create_line(t, 270, t, miny, arrow=tk.LAST)
            self.upids.add(id)
            c = self.canvas.coords(minid)
            self.canvas.coords(minid, c[0], c[1], t-1, c[3])

            # need to propagate
            if minid in self.pairs:
                c_to_replace = self.canvas.coords(self.pairs[minid])
                self.canvas.delete(self.pairs[minid])
                self.upids.remove(self.pairs[minid])
                del self.pairs[self.pairs[minid]]
                
                self.pairs[id] = minid
                self.pairs[minid] = id
                self.insert(c_to_replace[0], c_to_replace[1])
            else:
                self.pairs[id] = minid
                self.pairs[minid] = id

        #insert line
        else:
            mint = 601
            minid = -1
            for line in self.upids:
                c = self.canvas.coords(line)
                if c[3] <= y and c[1]>=y:
                    if c[0] < mint and c[0] > t:
                        mint = c[0]
                        minid = line
            
            # doesn't cross a line
            if minid == -1:
                id = self.canvas.create_line(t, y, 600, y, arrow=tk.LAST)
                id2 = self.canvas.create_oval(t-3, y-3, t+3, y+3, fill="black")
                self.crossids.add(id)
                self.linedotid[id] = id2

            # crosses a line
            else:
                id = self.canvas.create_line(t, y, mint-1, y, arrow=tk.LAST)
                id2 = self.canvas.create_oval(t-3, y-3, t+3, y+3, fill="black")
                self.crossids.add(id)
                self.linedotid[id] = id2
                c = self.canvas.coords(minid)
                self.canvas.coords(minid, c[0], c[1], c[2], y)

                # need to propagate
                if minid in self.pairs:
                    c_to_replace = self.canvas.coords(self.pairs[minid])
                    self.canvas.delete(self.pairs[minid])
                    self.canvas.delete(self.linedotid[self.pairs[minid]])
                    del self.linedotid[self.pairs[minid]]
                    self.crossids.remove(self.pairs[minid])
                    del self.pairs[self.pairs[minid]]
                    self.pairs[id] = minid
                    self.pairs[minid] = id
                    self.insert(c_to_replace[0], c_to_replace[1])
                else:
                    self.pairs[id] = minid
                    self.pairs[minid] = id



    def delete(self, t, y):
        # Delete a deletemin
        if y >= 270:
            if self.last_highlight != -1:
                self.canvas.delete(self.last_highlight)
                c_to_replace = self.canvas.coords(self.pairs[self.last_highlight])
                self.canvas.delete(self.pairs[self.last_highlight])
                self.canvas.delete(self.linedotid[self.pairs[self.last_highlight]])
                del self.linedotid[self.pairs[self.last_highlight]]
                self.upids.remove(self.last_highlight)
                self.crossids.remove(self.pairs[self.last_highlight])
                del self.pairs[self.pairs[self.last_highlight]]
                del self.pairs[self.last_highlight]
                self.last_highlight = -1
                self.insert(c_to_replace[0], c_to_replace[1])
                
        # Delete an insert
        else:
            if self.last_highlight != -1:
                self.canvas.delete(self.last_highlight)
                c_to_replace = self.canvas.coords(self.pairs[self.last_highlight])
                self.canvas.delete(self.pairs[self.last_highlight])
                self.canvas.delete(self.linedotid[self.last_highlight])
                del self.linedotid[self.last_highlight]
                self.crossids.remove(self.last_highlight)
                self.upids.remove(self.pairs[self.last_highlight])
                del self.pairs[self.pairs[self.last_highlight]]
                del self.pairs[self.last_highlight]
                self.last_highlight = -1
                self.insert(c_to_replace[0], c_to_replace[1])



Window()