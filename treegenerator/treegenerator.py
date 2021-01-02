from PIL import Image, ImageDraw, ImageTk, ImageChops
from random import random, seed
from math import cos, sin, radians, ceil, pi
from tkinter import Tk, Label, IntVar, DoubleVar, StringVar, Button, W, OptionMenu, BooleanVar
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename
from time import time
from os import urandom

root = Tk()
root.title("Treeinator")

mainframe = ttk.Frame(root)
mainframe.grid(column=0, row=0)

branch_chance_e = DoubleVar(value=0.1)
split_chance_e = DoubleVar(value=0.05)
branch_length_e = IntVar(value=20)
branch_taper_e = DoubleVar(value=0.02)
leaf_density_e = DoubleVar(value=0.7)
branch_mirror_e = DoubleVar(value=0.2)
branch_angle_e = DoubleVar(value=30)
angle_deviation_e = DoubleVar(value=0.6)
initial_width_e = IntVar(value=64)
max_branch_depth_e = IntVar(value=48)
min_branch_width_e = IntVar(value=4)
fruit_type_e = StringVar()
fruit_density_e = DoubleVar(value=0.4)
seed_e = IntVar(value=-1)
save_size_e = StringVar()
branch_attenuation_e = DoubleVar(value=1.2)
wind_e = DoubleVar(value=0)
branch_angle_rand_e = BooleanVar(value=True)
trunk_taper_e = DoubleVar(value=0.02)
colour_style_e = StringVar()
animate_e = BooleanVar(value=False)
animation_wiggle_e = DoubleVar(value=0.5)
grass_e = BooleanVar(value=True)
no_branch_grace_e = IntVar(value=0)

def set_seed():
    seed_value = int(random()*2**64)
    seed(seed_value)
    seed_e.set(seed_value)

set_seed()

save_sizes=["512x512", "256x256", "128x128"][::-1]

fruit_types = ["Apple", "Banana", "Berry"]
fruit_images = {"Banana": Image.open("banana.png"), "Apple": Image.open("apple.png"), "Berry": Image.open("berry.png")}

colour_styles = ["Oak", "Pine"]
bark_colours = {"Oak":(110, 82, 62, 255), "Pine": (102, 51, 0, 255)}
leaf_colours = {"Oak":(50, 168, 82), "Pine":(40, 120, 61)}
grass_colours = {"Oak":(108, 124, 0, 255),"Pine":(108, 124, 0, 255)}

ttk.Label(mainframe, text="800x800").grid(column=5, row=0, columnspan=15)
generated_image = ttk.Label(mainframe, borderwidth=2, relief="groove")
generated_image.grid(column=5,row=1,columnspan=15, rowspan=15)

ttk.Label(mainframe, text="512x512 (cubic filtered)").grid(column=20, row=0, columnspan=6)
generated_image2 = ttk.Label(mainframe)
generated_image2.grid(column=20,row=1,columnspan=6, rowspan=6)

ttk.Label(mainframe, text="256x256").grid(column=20, row=7, columnspan=3)
generated_image3 = ttk.Label(mainframe)
generated_image3.grid(column=20,row=8,columnspan=3, rowspan=3)

ttk.Label(mainframe, text="128x128").grid(column=23, row=7, columnspan=3)
generated_image4 = ttk.Label(mainframe)
generated_image4.grid(column=23,row=8,columnspan=3, rowspan=3)

leaf = Image.open("leaf.png")
leaves = [leaf.rotate(i*15, expand=1, resample=Image.NEAREST) for i in range(24)]

class Tree:
    def __init__(self, width, parent):
        self.width = width
        self.parent = parent
        self.left = None
        self.right = None
        self.middle = None

    def __repr__(self):
        return f"Tree({self.width},{self.left},{self.middle},{self.right})"

    def __str__(self):
        return self.__repr__()

def save():
    file = asksaveasfilename(defaultextension=".PNG", initialfile="tree.png")
    size = save_size_e.get()
    if size == "512x512" and generated_image2.image:
        generated_image2.image[1].save(file)
    elif size == "256x256" and generated_image3.image:
        generated_image3.image[1].save(file)
    elif size == "128x128" and generated_image4.image:
        generated_image4.image[1].save(file)

def save_animation():
    file = asksaveasfilename(defaultextension=".PNG", initialfile="tree_anim.png")
    anim = []
    size = save_size_e.get().split("x")
    resolution = (int(size[0]), int(size[1]))
    print("#"*64)
    for i in range(64):
        anim.append(gen(wind=i*pi/32, display=False).resize(resolution, resample=Image.NEAREST))
        print("#",end="")
    print()
    img = Image.new("RGBA", (resolution[0]*8, resolution[1]*8))
    for j in range(8):
        for i in range(8):
            img.paste(anim[j*8+i], (i*resolution[0], j*resolution[1]), anim[j*8+i])
            print("#",end="")
    print()
    img.save(file)
        

def gen(wind=0, display=True):
    angle = animation_wiggle_e.get()*sin(wind)
    #get variables
    branch_chance = branch_chance_e.get()
    split_chance = split_chance_e.get()
    branch_length = branch_length_e.get()
    trunk_taper = 1-trunk_taper_e.get()
    branch_taper = 1-branch_taper_e.get()
    leaf_density = 0.2*leaf_density_e.get()
    branch_mirror = branch_mirror_e.get()
    branch_angle = branch_angle_e.get()
    angle_deviation = 10*angle_deviation_e.get()
    initial_width = initial_width_e.get()
    max_branch_depth = max_branch_depth_e.get()
    min_branch_width = min_branch_width_e.get()
    fruit_type = fruit_type_e.get()
    fruit_density = 0.1*fruit_density_e.get()
    seed_value = seed_e.get()
    seed(seed_value)
    branch_attenuation = branch_attenuation_e.get()
    branch_angle_rand = branch_angle_rand_e.get()
    style = colour_style_e.get()
    branch_grace = no_branch_grace_e.get()
    
    # define functions
    def create_tree(parent,depth,branch_chance_modifier,core=False):
        if parent.width <= min_branch_width or depth > max_branch_depth:
            return
        
        stretch_factor = max(1, 3/parent.width)
        size_factor = branch_taper/stretch_factor
        branch_factor = (0.25*parent.width/initial_width)*(stretch_factor**2)

        split = random() < split_chance*branch_factor*branch_chance_modifier and depth >= branch_grace
        branch = not split and random() < branch_chance*branch_factor*branch_chance_modifier and depth >= branch_grace
        mirror = branch and random() < branch_mirror
        
        if split:
            t1 = Tree(parent.width*branch_taper*0.8, parent)
            create_tree(t1,depth+1,branch_attenuation*branch_chance_modifier)
            parent.left = t1
            t2 = Tree(parent.width*branch_taper*0.6, parent)
            create_tree(t2,depth+1,branch_attenuation*branch_chance_modifier)
            parent.right = t2
        else:
            t = Tree((trunk_taper if core else branch_taper)*parent.width*(0.9 if branch else 1), parent)
            create_tree(t,depth+1,branch_chance_modifier*1.2, core=core)
            parent.middle = t
            if branch:
                side = random() < 0.5 # True = left
                t1 = Tree(parent.width*branch_taper*0.5, parent)
                create_tree(t1,depth+1,branch_chance_modifier*branch_attenuation)
                if side:
                    parent.left = t1
                else:
                    parent.right = t1
                if mirror:
                    t2 = Tree(parent.width*branch_taper*0.5, parent)
                    create_tree(t2,depth+1,branch_chance_modifier*branch_attenuation)
                    if side:
                        parent.right = t2
                    else:
                        parent.left = t2

    def traverse(draw, img, tree, pos, ang, deviation):
        #below check might be good to use but idk
        if tree:
            if tree.width < leaf_density*initial_width:
                mod = (7+6*random())/10
                colour = leaf_colours[style]
                colour = (int(min(255,colour[0]*mod)), int(min(255,colour[1]*mod)), int(min(255,colour[2]*mod)), 255)
                tint = Image.new("RGBA", leaf.size, color=colour)
                restore_seed = int(random()*65536)
                for i in range(int(random()*64*leaf_density)):
                    npos = (int(pos[0] + 64*random()-32), int(pos[1] + 64*random()-32))
                    lf = ImageChops.multiply(leaves[int(random()*24)],tint)
                    img.paste(tint, npos, lf)
                seed(restore_seed)
                if random() < fruit_density:
                    npos = (int(pos[0] + 64*random()-32), int(pos[1] + 64*random()-32))
                    img.paste(fruit_images[fruit_type], npos, fruit_images[fruit_type])
                else:
                    random()
                    random()
            else:
                random()
                seed(int(random()*65536))
                random()
                random()
                random()
                
            deviation2 = deviation + random() * 2 * angle_deviation - angle_deviation
            ang2 = radians(ang + deviation2)
            x = sin(ang2)
            y = cos(ang2)
            prev_pos = (pos[0] - 0.2*branch_length*x, pos[1] + 0.2*branch_length*y)
            new_pos = (pos[0] + branch_length*x, pos[1] - branch_length*y)
            #draw.line([prev_pos, new_pos], fill=(102, 51, 0, 255), width=int(tree.width))
            hw = tree.width/2
            draw.polygon([(prev_pos[0]-y*hw, prev_pos[1]-x*hw),
                          (prev_pos[0]+y*hw, prev_pos[1]+x*hw),
                          (new_pos[0]+y*hw, new_pos[1]+x*hw),
                          (new_pos[0]-y*hw, new_pos[1]-x*hw)],
                         fill=bark_colours[style])
            #draw.line([prev_pos[0]+y*hw, prev_pos[1]+x*hw,
            #           new_pos[0]+y*hw, new_pos[1]+x*hw], fill=(0,0,0,200))
            #draw.line([prev_pos[0]-y*hw, prev_pos[1]-x*hw,
            #           new_pos[0]-y*hw, new_pos[1]-x*hw], fill=(0,0,0,255), width=2)
            if tree.left:
                traverse(draw, img, tree.left, (new_pos[0]-tree.width/4,new_pos[1]), ang-(0.5*(random()+1) if branch_angle_rand else 1)*branch_angle, deviation+angle)
            if tree.middle:
                traverse(draw, img, tree.middle, new_pos, ang, deviation2+angle) # new_pos if (tree.left and tree.right or (not tree.left and not tree.right)) else (new_pos[0]-tree.right.width/2,new_pos[1]) if tree.right else (new_pos[0]+tree.left.width/2,new_pos[1])
            if tree.right:
                traverse(draw, img, tree.right, (new_pos[0]+tree.width/4,new_pos[1]), ang+(0.5*(random()+1) if branch_angle_rand else 1)*branch_angle, deviation+angle)
    
    #generate tree
    t = Tree(initial_width,None)
    create_tree(t,1,1,core=True)

    img = Image.new("RGBA", (1024,1024), color=(1,1,1,0))
    draw = ImageDraw.Draw(img)
    start = (img.width/2,img.height)

    traverse(draw, img, t, start, 0, random() * 2 * angle_deviation - angle_deviation)

    if grass_e.get():
        for i in range(initial_width*2):
            mov = i - initial_width
            up_shift = mov + random()*initial_width/2 - initial_width/4
            draw.line([start[0]+mov, start[1], start[0]+up_shift, start[1]-initial_width+0.5*initial_width*random()], fill=grass_colours[style], width=2)
        
    if display:
        tkimg = ImageTk.PhotoImage(img.resize((800,800)))
        generated_image.configure(image=tkimg)
        generated_image.image = tkimg
        tkimg2 = ImageTk.PhotoImage(img.resize((512,512), resample=Image.CUBIC))
        generated_image2.configure(image=tkimg2)
        generated_image2.image = (tkimg2,img.resize((512,512), resample=Image.CUBIC))
        tkimg3 = ImageTk.PhotoImage(img.resize((256,256), resample=Image.NEAREST))
        generated_image3.configure(image=tkimg3)
        generated_image3.image = (tkimg3, img.resize((256,256), resample=Image.NEAREST))
        tkimg4 = ImageTk.PhotoImage(img.resize((128,128), resample=Image.NEAREST).resize((256,256), resample=Image.NEAREST))
        generated_image4.configure(image=tkimg4)
        generated_image4.image = (tkimg4, img.resize((128,128), resample=Image.NEAREST))

        if animate_e.get():
            root.after(100, lambda: gen(wind=wind+pi/64))
    return img
    

    

ttk.Label(mainframe, text="Branch Chance Modifier:").grid(column=0, row=0, sticky=(W))
ttk.Label(mainframe, text="Split Chance (0-1):").grid(column=0, row=1, sticky=(W))
ttk.Label(mainframe, text="Branch Length (px):").grid(column=0, row=2, sticky=(W))
ttk.Label(mainframe, text="Branch Taper (0-1):").grid(column=0, row=3, sticky=(W))
ttk.Label(mainframe, text="Leaf Density (0-1):").grid(column=0, row=4, sticky=(W))
ttk.Label(mainframe, text="Branch Mirror (0-1):").grid(column=0, row=5, sticky=(W))
ttk.Label(mainframe, text="Branch Angle (0-90):").grid(column=0, row=6, sticky=(W))
ttk.Label(mainframe, text="Randomise Branch Angle:").grid(column=0, row=7, sticky=(W))
ttk.Label(mainframe, text="Angle Deviation (0-1):").grid(column=0, row=8, sticky=(W))
ttk.Label(mainframe, text="Initial Width (px):").grid(column=0, row=9, sticky=(W))
ttk.Label(mainframe, text="Max Branch Depth (nat):").grid(column=0, row=10, sticky=(W))
ttk.Label(mainframe, text="Min Branch Width (px):").grid(column=0, row=11, sticky=(W))
ttk.Label(mainframe, text="Branching Coefficient:").grid(column=0, row=12, sticky=(W))
ttk.Label(mainframe, text="Fruit:").grid(column=0, row=13, sticky=(W))
ttk.Label(mainframe, text="Fruit Density (0-1):").grid(column=0, row=14, sticky=(W))
ttk.Label(mainframe, text="Trunk Taper (0-1):").grid(column=0, row=15, sticky=(W))
ttk.Label(mainframe, text="Colour Style:").grid(column=0, row=16, sticky=(W))

ttk.Label(mainframe, text="Animation Strength:").grid(column=3, row=0, sticky=(W))
ttk.Label(mainframe, text="Grass Base:").grid(column=3, row=1, sticky=(W))
ttk.Label(mainframe, text="Branch Grace Depth (nat):").grid(column=3, row=2, sticky=(W))


ttk.Label(mainframe, text="Seed (int):").grid(column=0, row=18, sticky=(W))
ttk.Label(mainframe, text="Save Size:").grid(column=0, row=19, sticky=(W))

ttk.Entry(mainframe, textvariable=branch_chance_e).grid(column=1, row=0, sticky=(W), columnspan=2)
ttk.Entry(mainframe, textvariable=split_chance_e).grid(column=1, row=1, sticky=(W), columnspan=2)
ttk.Entry(mainframe, textvariable=branch_length_e).grid(column=1, row=2, sticky=(W), columnspan=2)
ttk.Entry(mainframe, textvariable=branch_taper_e).grid(column=1, row=3, sticky=(W), columnspan=2)
ttk.Entry(mainframe, textvariable=leaf_density_e).grid(column=1, row=4, sticky=(W), columnspan=2)
ttk.Entry(mainframe, textvariable=branch_mirror_e).grid(column=1, row=5, sticky=(W), columnspan=2)
ttk.Entry(mainframe, textvariable=branch_angle_e).grid(column=1, row=6, sticky=(W), columnspan=2)
ttk.Checkbutton(mainframe, variable=branch_angle_rand_e).grid(column=1, row=7, sticky=(W))
ttk.Entry(mainframe, textvariable=angle_deviation_e).grid(column=1, row=8, sticky=(W), columnspan=2)
ttk.Entry(mainframe, textvariable=initial_width_e).grid(column=1, row=9, sticky=(W), columnspan=2)
ttk.Entry(mainframe, textvariable=max_branch_depth_e).grid(column=1, row=10, sticky=(W), columnspan=2)
ttk.Entry(mainframe, textvariable=min_branch_width_e).grid(column=1, row=11, sticky=(W), columnspan=2)
ttk.Entry(mainframe, textvariable=branch_attenuation_e).grid(column=1, row=12, sticky=(W), columnspan=2)
ttk.OptionMenu(mainframe, fruit_type_e, fruit_types[0], *fruit_types).grid(column=1, row=13, sticky=(W), columnspan=2)
ttk.Entry(mainframe, textvariable=fruit_density_e).grid(column=1, row=14, sticky=(W), columnspan=2)
ttk.Entry(mainframe, textvariable=trunk_taper_e).grid(column=1, row=15, sticky=(W), columnspan=2)
ttk.OptionMenu(mainframe, colour_style_e, colour_styles[0], *colour_styles).grid(column=1, row=16, sticky=(W), columnspan=2)

ttk.Entry(mainframe, textvariable=animation_wiggle_e).grid(column=4, row=0, sticky=(W))
ttk.Checkbutton(mainframe, variable=grass_e).grid(column=4, row=1, sticky=(W))
ttk.Entry(mainframe, textvariable=no_branch_grace_e).grid(column=4, row=2, sticky=(W))


ttk.Entry(mainframe, textvariable=seed_e).grid(column=1, row=18, sticky=(W), columnspan=2)
ttk.OptionMenu(mainframe, save_size_e, save_sizes[1], *save_sizes).grid(column=1, row=19, sticky=(W), columnspan=2)

ttk.Button(mainframe, text="Regenerate", command=lambda:[x() for x in [lambda:animate_e.set(False),gen]]).grid(column=1, row=20, sticky=W)
ttk.Button(mainframe, text="Random Seed", command=lambda:[x() for x in [lambda:animate_e.set(False), set_seed, gen]]).grid(column=2, row=20, sticky=W)
ttk.Button(mainframe, text="Animate", command=lambda:[x() for x in [lambda:animate_e.set(True), gen]] if not animate_e.get() else None).grid(column=3, row=20, sticky=W)
ttk.Button(mainframe, text="Save", command=save).grid(column=0, row=20, sticky=W)
ttk.Button(mainframe, text="Save Animation", command=save_animation).grid(column=4, row=20, sticky=W)

root.mainloop()
