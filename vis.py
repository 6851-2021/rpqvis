import tkinter as tk
import time


class Window:
    def __init__(self):
        self.vertical_space = 50
        self.horizontal_space = 100

        self.crossids = set()
        self.upids = set()
        self.mode = "insert"
        self.step = False

        self.ghost_ray = None
        self.ghost_dot = None

        self.linedotid = {}

        self.line_quantized_coords = {}
        self.dot_quantized_coords = {}

        # no lines allowed on same coordinates
        self.taken_x = set()
        self.taken_y = set()

        self.last_toggle = 0
        self.query_id = None
        self.window = tk.Tk()

        self.window.geometry("600x300")
        self.window.minsize(300, 150)
        self.canvas = tk.Canvas(self.window, width=600, height=300)
        self.canvas.bind("<Button-1>", self.clicked)
        self.window.bind("<d>", self.toggle)
        self.window.bind("<i>", self.toggle)
        self.window.bind("<q>", self.toggle)
        self.window.bind("<s>", self.toggle)
        self.window.bind("<Configure>", self.resize)
        self.canvas.pack()

        self.bottom_rect = self.canvas.create_rectangle(0, 270, 600, 350, fill="black")
        self.canvas.addtag_all("all")
        self.pairs = dict()

        self.canvas.bind('<Motion>', self.motion)
        self.last_highlight = -1
        self.w = 600
        self.h = 300

        self.window.mainloop()

    def quantize(self, t, y, w, h):
        qt = round(t/w*self.horizontal_space)
        qy = round(y/h*self.vertical_space)
        return qt, qy

    def quantize_line(self, c, w, h):
        pt1 = self.quantize(c[0], c[1], w, h)
        pt2 = self.quantize(c[2], c[3], w, h)
        return (pt1[0], pt1[1], pt2[0], pt2[1])

    def unquantize(self, qt, qy, w, h):
        t = round(qt/self.horizontal_space*w)
        y = round(qy/self.vertical_space*h)
        return t, y

    def display_line(self, qt1, qy1, qt2, qy2, fill="black"):
        t1, y1 = self.unquantize(qt1, qy1, self.w, self.h)
        t2, y2 = self.unquantize(qt2, qy2, self.w, self.h)

        id = self.canvas.create_line(t1, y1, t2, y2, arrow=tk.LAST, fill=fill)
        return id

    def display_dot(self, qt, qy, fill="black", outline="black"):
        t, y = self.unquantize(qt, qy, self.w, self.h)
        id = self.canvas.create_oval(t-3, y-3, t+3, y+3, fill=fill, outline=outline)
        return id

    def scale_line(self, id):
        c = self.line_quantized_coords[id]
        pt1 = self.unquantize(c[0], c[1], self.w, self.h)
        pt2 = self.unquantize(c[2], c[3], self.w, self.h)
        
        self.canvas.coords(id, pt1[0], pt1[1], pt2[0], pt2[1])

    def scale_dot(self, id):
        c = self.dot_quantized_coords[id]
        pt1 = self.unquantize(c[0], c[1], self.w, self.h)
        self.canvas.coords(id, pt1[0]+3, pt1[1]+3, pt1[0]-3, pt1[1]-3)

    def query(self, t):
        existlist = []
        for line in self.crossids:
            c = self.line_quantized_coords[line]
            if c[2] > t and c[0] <= t:
                existlist.append(c[1])

        return sorted(existlist, reverse=True)

    def resize(self, event):
        
        rw = float(event.width)/self.w
        rh = float(event.height)/self.h
        
        # resize the canvas 
        self.canvas.config(width=event.width, height=event.height)
        # rescale all the objects tagged with the "all" tag
        self.canvas.scale("all", 0, 0, rw, rh)

        self.w = event.width
        self.h = event.height

        for line in self.crossids:
            self.scale_line(line)

        for line in self.upids:
            self.scale_line(line)

        for k in self.linedotid:
            dot = self.linedotid[k]
            self.scale_dot(dot)

    def check_propagate_error(self, id):
        # insert a delete-min
        [t, y, _, _] = self.line_quantized_coords[id]
        if y >= 9/10*self.vertical_space:
            miny = -1
            minid = -1
            for line in self.crossids:
                c = self.line_quantized_coords[line]
                if c[0] <= t and c[2]>t:
                    if c[1] > miny:
                        miny = c[1]
                        minid = line

            if miny < 0:
                return True
            else:
                if minid in self.pairs:
                    return self.check_propagate_error(self.pairs[minid])
                else:
                    return False


    def motion(self, event):
        
        if self.query_id is not None:
            self.canvas.delete(self.query_id)
            self.query_id = None

        if self.mode == "query":
            t, y = self.quantize(event.x, event.y, self.w, self.h)
            curr_queue = self.query(t)
            curr_min = 0
            # TODO: magic numbers here, remove when resize done
            if len(curr_queue) > 0:
                curr_min = curr_queue[0]
            self.query_id = self.display_line(t, 9/10*self.vertical_space, t, curr_min)
            
            # self.canvas.create_line(event.x, 9/10*self.h, event.x, curr_min, arrow=tk.LAST)
            self.canvas.itemconfig(self.query_id, fill='green')

        # color changes on hover, for "Delete" events only
        elif self.mode == "delete":
            t, y = self.quantize(event.x, event.y, self.w, self.h)
    
            closest = -1
            dist = float('inf')
            linetype = None
            for line in self.crossids:
                c = self.line_quantized_coords[line]
                if c[1] <= y+1 and c[1]>=y-1 and c[0] <= t and c[2] >= t:
                    if abs(y-c[1]) < dist:
                        closest = line
                        dist = abs(y-c[1])
                        linetype = "cross"
            
            for line in self.upids:
                c = self.line_quantized_coords[line]
                if c[0] <= t+1 and c[0]>=t-1 and c[3] <= y and c[1] >= y:
                    if abs(t-c[0]) < dist:
                        closest = line
                        dist = abs(t-c[0])
                        linetype = "up"

            if closest >= 0:
                if self.last_highlight != -1 and self.last_highlight != closest:
                    self.canvas.itemconfig(self.last_highlight, fill='black')
                else:
                    if linetype == "up":
                        self.canvas.itemconfig(closest, fill='light grey')
                    elif linetype == "cross":
                        if closest in self.pairs and self.check_propagate_error(self.pairs[closest]):
                            self.canvas.itemconfig(closest, fill='red')
                            self.canvas.itemconfig(self.linedotid[closest], fill='red', outline='red')
                        else:
                            self.canvas.itemconfig(closest, fill='light grey')
                            self.canvas.itemconfig(self.linedotid[closest], fill='light grey', outline='light grey')
                            
                self.last_highlight = closest

            else:
                if self.last_highlight != -1:
                    self.canvas.itemconfig(self.last_highlight, fill='black')
                    if self.last_highlight in self.crossids:
                        self.canvas.itemconfig(self.linedotid[self.last_highlight], fill='black', outline='black')
                self.last_highlight = -1

        elif self.mode == "insert":
            t, y = self.quantize(event.x, event.y, self.w, self.h)
            
            linecoords = []

            # turn ghost red if coordinate is taken
            red = False
            if t in self.taken_x or y in self.taken_y:
                red = True

            # insert a delete-min
            if y >= 9/10*self.vertical_space:
                miny = -1
                minid = -1
                for line in self.crossids:
                    c = self.line_quantized_coords[line]
                    if c[0] <= t and c[2]>=t:
                        if c[1] > miny:
                            miny = c[1]
                            minid = line

                if miny < 0:
                    linecoords = [t, round(9/10*self.vertical_space), t, 0]
                    red = True
                else:
                    linecoords = [t, round(9/10*self.vertical_space), t, miny]
                    if minid in self.pairs:
                        red = self.check_propagate_error(self.pairs[minid])

            #insert line
            else:
                mint = self.w + 1
                minid = -1
                for line in self.upids:
                    c = self.line_quantized_coords[line]
                    if c[3] <= y and c[1]>=y:
                        if c[0] < mint and c[0] > t:
                            mint = c[0]
                            minid = line

                # doesn't cross a line
                if minid == -1:
                    linecoords = [t, y, self.horizontal_space, y]
                # crosses a line
                else:
                    linecoords = [t, y, mint, y]

            if self.ghost_ray is None:
                if red:
                    self.ghost_ray = self.display_line(linecoords[0], linecoords[1], linecoords[2], linecoords[3], fill="red")
                else:
                    self.ghost_ray = self.display_line(linecoords[0], linecoords[1], linecoords[2], linecoords[3], fill="light grey")
            else:
                pt1 = self.unquantize(linecoords[0], linecoords[1], self.w, self.h)
                pt2 = self.unquantize(linecoords[2], linecoords[3], self.w, self.h)
        
                self.canvas.coords(self.ghost_ray, pt1[0], pt1[1], pt2[0], pt2[1])

                if red:
                    self.canvas.itemconfig(self.ghost_ray, fill='red')
                else:
                    self.canvas.itemconfig(self.ghost_ray, fill='light grey')

            if y >= 9/10*self.vertical_space:
                if self.ghost_dot is not None:
                    self.canvas.delete(self.ghost_dot)
                    self.ghost_dot = None
            elif self.ghost_dot is None:
                if red:
                    self.ghost_dot = self.display_dot(linecoords[0], linecoords[1], fill="red", outline="red")
                else:
                    self.ghost_dot = self.display_dot(linecoords[0], linecoords[1], fill="light grey", outline="light grey")
            else:
                pt = self.unquantize(linecoords[0], linecoords[1], self.w, self.h)        
                self.canvas.coords(self.ghost_dot, pt[0]+3, pt[1]+3, pt[0]-3, pt[1]-3)
                if red:
                    self.canvas.itemconfig(self.ghost_dot, fill='red', outline='red')
                else:
                    self.canvas.itemconfig(self.ghost_dot, fill='light grey', outline='light grey')


    def clicked(self, event):
        x, y = self.quantize(event.x, event.y, self.w, self.h)

        # avoid drawing lines too close to edge
        if (x < 4 or x > self.horizontal_space-4) and (y < 4 or y > self.vertical_space - 4) and (event.x < 24 or event.x > self.w - 24) and (event.y < 24 or event.y > self.h - 24):
            return

        if self.mode == "query":
            print([round(9/10*self.vertical_space-l) for l in self.query(x)])
        elif self.mode == "insert":
            self.insert(x, y)
        elif self.mode == "delete":
            self.delete(x, y)

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
            elif event.keysym == "s":
                self.step = not self.step
                print("step-through: ", self.step)
            if self.last_highlight != -1:
                self.canvas.itemconfig(self.last_highlight, fill='black')
            if self.ghost_ray is not None:
                self.canvas.delete(self.ghost_ray)
                self.ghost_ray = None
            self.last_highlight = -1

    def insert(self, t, y):
        # don't allow same coords
        if t in self.taken_x or y in self.taken_y:
            return
        # "Insert" of a delete-min event of value y at time t
        if y >= 9/10*self.vertical_space:
            miny = -1
            minid = -1
            for line in self.crossids:
                c = self.line_quantized_coords[line]
                if c[0] <= t and c[2]>=t:
                    if c[1] > miny:
                        miny = c[1]
                        minid = line
            
            if miny < 0:
                print("No min to delete")
                return
            elif minid in self.pairs:
                if self.check_propagate_error(self.pairs[minid]):
                    return
            
            id = self.display_line(t, round(9/10*self.vertical_space), t, miny)
            self.upids.add(id)

            self.line_quantized_coords[id] = [t, round(9/10*self.vertical_space), t, miny]
            c = self.line_quantized_coords[minid]
            self.taken_x.add(t)
            self.line_quantized_coords[minid][2] = t
            self.scale_line(minid)
            # need to propagate
            if minid in self.pairs:
                c_to_replace = self.line_quantized_coords[self.pairs[minid]]
                self.canvas.delete(self.pairs[minid])
                del self.line_quantized_coords[self.pairs[minid]]
                self.taken_x.remove(c_to_replace[0])

                self.upids.remove(self.pairs[minid])
                del self.pairs[self.pairs[minid]]
                
                self.pairs[id] = minid
                self.pairs[minid] = id
                if self.step:
                    self.canvas.after(100, lambda: self.insert(c_to_replace[0], c_to_replace[1]))
                else:
                    self.insert(c_to_replace[0], c_to_replace[1])
            else:
                self.pairs[id] = minid
                self.pairs[minid] = id

        #insert line
        else:
            mint = self.w + 1
            minid = -1
            for line in self.upids:
                c = self.line_quantized_coords[line]
                if c[3] <= y and c[1]>=y:
                    if c[0] < mint and c[0] > t:
                        mint = c[0]
                        minid = line

            # doesn't cross a line
            if minid == -1:
                id = self.display_line(t, y, self.horizontal_space, y)
                self.line_quantized_coords[id] = [t, y, self.horizontal_space, y]
                id2 = self.display_dot(t, y)
                self.crossids.add(id)
                self.dot_quantized_coords[id2] = [t, y]
                self.linedotid[id] = id2
                self.taken_x.add(t)
                self.taken_y.add(y)

            # crosses a line
            else:
                id = self.display_line(t, y, mint, y)
                id2 = self.display_dot(t, y)
                self.line_quantized_coords[id] = [t, y, mint, y]
                self.crossids.add(id)
                self.linedotid[id] = id2
                self.taken_x.add(t)
                self.taken_y.add(y)
                self.dot_quantized_coords[id2] = [t, y]
                self.line_quantized_coords[minid][3] = y
                self.scale_line(minid)

                # need to propagate
                if minid in self.pairs:
                    c_to_replace = self.line_quantized_coords[self.pairs[minid]]
                    self.canvas.delete(self.pairs[minid])
                    del self.line_quantized_coords[self.pairs[minid]]

                    self.canvas.delete(self.linedotid[self.pairs[minid]])
                    del self.dot_quantized_coords[self.linedotid[self.pairs[minid]]]
                    del self.linedotid[self.pairs[minid]]
                    self.taken_x.remove(c_to_replace[0])
                    self.taken_y.remove(c_to_replace[1])
                    
                    self.crossids.remove(self.pairs[minid])
                    del self.pairs[self.pairs[minid]]
                    self.pairs[id] = minid
                    self.pairs[minid] = id
                    if self.step:
                        self.canvas.after(100, lambda: self.insert(c_to_replace[0], c_to_replace[1]))
                    else:
                        self.insert(c_to_replace[0], c_to_replace[1])
                else:
                    self.pairs[id] = minid
                    self.pairs[minid] = id


    def delete(self, t, y):
        # Delete a deletemin
        if self.last_highlight in self.upids:
            if self.last_highlight != -1:
                self.canvas.delete(self.last_highlight)
                c = self.line_quantized_coords[self.last_highlight]
                del self.line_quantized_coords[self.last_highlight]
                self.taken_x.remove(c[0])

                c_to_replace = self.line_quantized_coords[self.pairs[self.last_highlight]]
                self.canvas.delete(self.pairs[self.last_highlight])
                del self.line_quantized_coords[self.pairs[self.last_highlight]]
                
                self.crossids.remove(self.pairs[self.last_highlight])
                self.canvas.delete(self.linedotid[self.pairs[self.last_highlight]])
                self.taken_x.remove(c_to_replace[0])
                self.taken_y.remove(c_to_replace[1])
                del self.linedotid[self.pairs[self.last_highlight]]

                self.upids.remove(self.last_highlight)
                del self.pairs[self.pairs[self.last_highlight]]
                del self.pairs[self.last_highlight]
                self.last_highlight = -1
                if self.step:
                    self.canvas.after(100, lambda: self.insert(c_to_replace[0], c_to_replace[1]))
                else:
                    self.insert(c_to_replace[0], c_to_replace[1])

        # Delete an insert
        else:
            if self.last_highlight != -1:
                # has pair; need to propagate
                if self.last_highlight in self.pairs:
                    if self.check_propagate_error(self.pairs[self.last_highlight]):
                        return

                    self.canvas.delete(self.last_highlight)
                    c = self.line_quantized_coords[self.last_highlight]
                    self.taken_x.remove(c[0])
                    self.taken_y.remove(c[1])
                    del self.line_quantized_coords[self.last_highlight]
                    
                    c_to_replace = self.line_quantized_coords[self.pairs[self.last_highlight]]
                    self.canvas.delete(self.pairs[self.last_highlight])
                    self.canvas.delete(self.linedotid[self.last_highlight])
                    del self.linedotid[self.last_highlight]
                    self.crossids.remove(self.last_highlight)
                    self.upids.remove(self.pairs[self.last_highlight])
                    del self.pairs[self.pairs[self.last_highlight]]
                    del self.pairs[self.last_highlight]
                    self.last_highlight = -1
                    self.taken_x.remove(c_to_replace[0])
                    if self.step:
                        self.canvas.after(100, lambda: self.insert(c_to_replace[0], c_to_replace[1]))
                    else:
                        self.insert(c_to_replace[0], c_to_replace[1])

                # doesn't have pair
                else:
                    self.canvas.delete(self.last_highlight)
                    c = self.line_quantized_coords[self.last_highlight]
                    self.taken_x.remove(c[0])
                    self.taken_y.remove(c[1])
                    del self.line_quantized_coords[self.last_highlight]

                    self.canvas.delete(self.linedotid[self.last_highlight])
                    del self.dot_quantized_coords[self.linedotid[self.last_highlight]]
                    del self.linedotid[self.last_highlight]
                    self.crossids.remove(self.last_highlight)
                    
                    
                    self.last_highlight = -1




Window()
